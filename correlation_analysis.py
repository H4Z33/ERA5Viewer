"""
Multivariate Correlation Analysis Module for ERA5-Land Variables.
Supports the CHSI article by characterizing t2m ↔ swvl1 ↔ pev relationships
at sub-daily, daily, monthly, and annual scales.

Author: Raul Alejandro Morales Rivera, DCI, Posgrado FIT
"""

import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats, signal
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler
import sqlite3
import io
import base64
import warnings
import logging
from pathlib import Path

warnings.filterwarnings('ignore')
sns.set_theme(style="whitegrid")
logger = logging.getLogger("correlation_analysis")

DB_PATH = Path("era5_stats.db")

# --- Variable metadata ---
VAR_META = {
    "t2m":   {"label": "Temperatura 2m",          "units": "°C",     "convert": lambda x: x - 273.15},
    "swvl1": {"label": "Humedad Suelo L1",         "units": "m³/m³",  "convert": lambda x: x},
    "pev":   {"label": "Evaporación Potencial",     "units": "m",      "convert": lambda x: x},
}


def load_multivariate_df(db_path=DB_PATH, resample_freq=None):
    """Load all three variables as a time-indexed DataFrame from the stats DB."""
    with sqlite3.connect(db_path) as conn:
        df_raw = pd.read_sql_query(
            "SELECT variable, time_str, mean FROM hourly_stats", conn
        )
    
    df_pivot = df_raw.pivot(index='time_str', columns='variable', values='mean')
    df_pivot.index = pd.to_datetime(df_pivot.index)
    df_pivot.sort_index(inplace=True)
    
    # Apply unit conversions
    for var, meta in VAR_META.items():
        if var in df_pivot.columns:
            df_pivot[var] = meta["convert"](df_pivot[var])
    
    # Optional resampling
    if resample_freq:
        df_pivot = df_pivot.resample(resample_freq).mean()
    
    df_pivot.dropna(inplace=True)
    return df_pivot


def compute_correlation_matrix(df, method="pearson"):
    """Compute correlation matrix with p-values."""
    cols = [c for c in ["t2m", "swvl1", "pev"] if c in df.columns]
    n = len(cols)
    corr = pd.DataFrame(np.zeros((n, n)), index=cols, columns=cols)
    pval = pd.DataFrame(np.zeros((n, n)), index=cols, columns=cols)
    
    for i, c1 in enumerate(cols):
        for j, c2 in enumerate(cols):
            if i == j:
                corr.iloc[i, j] = 1.0
                pval.iloc[i, j] = 0.0
            else:
                if method == "pearson":
                    r, p = stats.pearsonr(df[c1], df[c2])
                elif method == "spearman":
                    r, p = stats.spearmanr(df[c1], df[c2])
                else:
                    r, p = stats.kendalltau(df[c1], df[c2])
                corr.iloc[i, j] = r
                pval.iloc[i, j] = p
    
    return corr, pval


def seasonal_correlation(df):
    """Compute correlation matrices by meteorological season."""
    seasons = {
        "DJF (Invierno)": [12, 1, 2],
        "MAM (Primavera)": [3, 4, 5],
        "JJA (Verano)":    [6, 7, 8],
        "SON (Otoño)":     [9, 10, 11],
    }
    results = {}
    for name, months in seasons.items():
        mask = df.index.month.isin(months)
        if mask.sum() > 30:
            corr, pval = compute_correlation_matrix(df[mask])
            results[name] = {"corr": corr, "pval": pval, "n": int(mask.sum())}
    return results


def cross_correlation_with_lag(df, var_x, var_y, max_lag_hours=72):
    """Compute cross-correlation between two variables with temporal lags."""
    x = df[var_x].values
    y = df[var_y].values
    
    # Normalize
    x = (x - np.mean(x)) / np.std(x)
    y = (y - np.mean(y)) / np.std(y)
    
    lags = range(-max_lag_hours, max_lag_hours + 1)
    cc = []
    for lag in lags:
        if lag >= 0:
            cc.append(np.corrcoef(x[lag:], y[:len(y)-lag])[0, 1] if lag < len(x) else 0)
        else:
            cc.append(np.corrcoef(x[:len(x)+lag], y[-lag:])[0, 1] if -lag < len(y) else 0)
    
    return list(lags), cc


def pca_analysis(df):
    """Run PCA on the three variables to identify dominant modes."""
    cols = [c for c in ["t2m", "swvl1", "pev"] if c in df.columns]
    X = df[cols].dropna().values
    
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    pca = PCA(n_components=len(cols))
    scores = pca.fit_transform(X_scaled)
    
    return {
        "explained_variance_ratio": pca.explained_variance_ratio_.tolist(),
        "components": pd.DataFrame(
            pca.components_, 
            columns=cols, 
            index=[f"PC{i+1}" for i in range(len(cols))]
        ),
        "scores": scores,
        "scaler": scaler,
        "pca": pca,
    }


def compute_annual_trends(df):
    """Compute annual means and Mann-Kendall trend per variable."""
    annual = df.resample("YE").mean()
    trends = {}
    for col in ["t2m", "swvl1", "pev"]:
        if col not in annual.columns:
            continue
        y = annual[col].dropna().values
        x = np.arange(len(y))
        slope, intercept, r, p, se = stats.linregress(x, y)
        trends[col] = {
            "slope_per_year": slope,
            "r_squared": r**2,
            "p_value": p,
            "significant": p < 0.05,
        }
    return annual, trends


def compute_anomalies(df, climatology_freq="ME"):
    """Compute anomalies relative to the long-term monthly/daily climatology."""
    climatology = df.groupby([df.index.month, df.index.day]).mean() if climatology_freq == "D" else df.groupby(df.index.month).mean()
    
    anomalies = df.copy()
    for col in df.columns:
        if climatology_freq == "D":
            clim_vals = df.groupby([df.index.month, df.index.day])[col].transform("mean")
        else:
            clim_vals = df.groupby(df.index.month)[col].transform("mean")
        anomalies[col] = df[col] - clim_vals
    
    return anomalies


# ============================================================
# Visualization Functions
# ============================================================

def _fig_to_base64(fig):
    buf = io.BytesIO()
    fig.savefig(buf, format='png', dpi=140, bbox_inches='tight')
    buf.seek(0)
    img_str = base64.b64encode(buf.read()).decode('utf-8')
    plt.close(fig)
    return img_str


def plot_correlation_heatmap(corr, title="Correlation Matrix", annot_pval=None):
    """Generate a styled correlation heatmap."""
    fig, ax = plt.subplots(figsize=(8, 6))
    
    labels = [VAR_META.get(c, {}).get("label", c) for c in corr.columns]
    mask = np.triu(np.ones_like(corr, dtype=bool), k=1)
    
    sns.heatmap(
        corr, annot=True, fmt=".3f", cmap="RdBu_r", center=0,
        vmin=-1, vmax=1, ax=ax, xticklabels=labels, yticklabels=labels,
        linewidths=1, square=True, cbar_kws={"shrink": 0.8}
    )
    ax.set_title(title, fontsize=14, fontweight='bold', pad=15)
    return fig


def plot_seasonal_heatmaps(seasonal_results):
    """Generate a 2x2 grid of seasonal correlation heatmaps."""
    fig, axes = plt.subplots(2, 2, figsize=(14, 12))
    axes = axes.flatten()
    
    for i, (season, data) in enumerate(seasonal_results.items()):
        labels = [VAR_META.get(c, {}).get("label", c) for c in data["corr"].columns]
        sns.heatmap(
            data["corr"], annot=True, fmt=".3f", cmap="RdBu_r", center=0,
            vmin=-1, vmax=1, ax=axes[i], xticklabels=labels, yticklabels=labels,
            linewidths=1, square=True
        )
        axes[i].set_title(f"{season} (n={data['n']:,})", fontsize=11, fontweight='bold')
    
    fig.suptitle("Correlación Estacional entre Variables Hidro-Climáticas", fontsize=14, fontweight='bold', y=1.02)
    plt.tight_layout()
    return fig


def plot_cross_correlation(lags, cc, var_x, var_y):
    """Plot cross-correlation function with lag."""
    fig, ax = plt.subplots(figsize=(12, 5))
    ax.bar(lags, cc, width=1.0, color="#38bdf8", alpha=0.7, edgecolor="none")
    ax.axhline(0, color='gray', linewidth=0.5)
    ax.axvline(0, color='red', linewidth=1, linestyle='--', alpha=0.5)
    
    peak_lag = lags[np.argmax(np.abs(cc))]
    peak_val = cc[np.argmax(np.abs(cc))]
    ax.annotate(f"Peak: lag={peak_lag}h, r={peak_val:.3f}",
                xy=(peak_lag, peak_val), fontsize=10, fontweight='bold',
                arrowprops=dict(arrowstyle="->", color="red"),
                xytext=(peak_lag + 10, peak_val * 0.8))
    
    lx = VAR_META.get(var_x, {}).get("label", var_x)
    ly = VAR_META.get(var_y, {}).get("label", var_y)
    ax.set_title(f"Cross-Correlation: {lx} → {ly}", fontsize=13, fontweight='bold')
    ax.set_xlabel("Lag (horas)")
    ax.set_ylabel("Correlación")
    ax.grid(True, alpha=0.3)
    return fig


def plot_pca_biplot(pca_result, df):
    """Generate PCA biplot showing loadings and explained variance."""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
    
    # Scree plot
    evr = pca_result["explained_variance_ratio"]
    cumulative = np.cumsum(evr)
    ax1.bar(range(1, len(evr)+1), [v*100 for v in evr], color="#818cf8", alpha=0.8, label="Individual")
    ax1.plot(range(1, len(evr)+1), [v*100 for v in cumulative], 'ro-', label="Acumulada")
    ax1.set_xlabel("Componente Principal")
    ax1.set_ylabel("Varianza Explicada (%)")
    ax1.set_title("Scree Plot", fontweight='bold')
    ax1.legend()
    ax1.set_xticks(range(1, len(evr)+1))
    
    # Loadings plot
    components = pca_result["components"]
    cols = components.columns
    colors = ["#ef4444", "#38bdf8", "#22c55e"]
    x = np.arange(len(cols))
    width = 0.25
    for i, pc in enumerate(components.index):
        ax2.bar(x + i*width, components.loc[pc], width, label=pc, color=colors[i], alpha=0.8)
    
    labels = [VAR_META.get(c, {}).get("label", c) for c in cols]
    ax2.set_xticks(x + width)
    ax2.set_xticklabels(labels)
    ax2.set_ylabel("Loading")
    ax2.set_title("Component Loadings", fontweight='bold')
    ax2.legend()
    ax2.axhline(0, color='gray', linewidth=0.5)
    
    plt.tight_layout()
    return fig


def plot_annual_trends(annual, trends):
    """Plot annual mean trends with regression lines."""
    fig, axes = plt.subplots(3, 1, figsize=(14, 12), sharex=True)
    
    for i, (col, ax) in enumerate(zip(["t2m", "swvl1", "pev"], axes)):
        if col not in annual.columns:
            continue
        meta = VAR_META.get(col, {})
        years = annual.index.year
        values = annual[col].values
        
        ax.plot(years, values, 'o-', color="#38bdf8", linewidth=2, markersize=4)
        
        # Regression line
        t = trends.get(col, {})
        if t:
            x = np.arange(len(years))
            y_fit = t["slope_per_year"] * x + (values[0] - t["slope_per_year"] * 0)
            slope, _, r2, p = t["slope_per_year"], None, t["r_squared"], t["p_value"]
            sig = "★" if t["significant"] else ""
            ax.plot(years, np.polyval(np.polyfit(x, values, 1), x), '--', color="#ef4444", linewidth=2)
            ax.set_title(
                f"{meta.get('label', col)} — Δ={slope:+.4f}/año, R²={r2:.3f}, p={p:.4f} {sig}",
                fontsize=11, fontweight='bold'
            )
        
        ax.set_ylabel(meta.get("units", ""))
        ax.grid(True, alpha=0.3)
    
    axes[-1].set_xlabel("Año")
    fig.suptitle("Tendencias Anuales (1998–2025)", fontsize=14, fontweight='bold', y=1.01)
    plt.tight_layout()
    return fig


# ============================================================
# HTML Report Generator
# ============================================================

def generate_correlation_html_report():
    """Generate a full HTML correlation analysis report."""
    logger.info("Loading multivariate data...")
    df_hourly = load_multivariate_df()
    df_daily = load_multivariate_df(resample_freq="1D")
    df_monthly = load_multivariate_df(resample_freq="1ME")
    
    sections = []
    
    # 1. Multi-scale correlation matrices
    for label, df, method in [
        ("Horaria (Pearson)", df_hourly, "pearson"),
        ("Diaria (Pearson)", df_daily, "pearson"),
        ("Mensual (Pearson)", df_monthly, "pearson"),
        ("Mensual (Spearman)", df_monthly, "spearman"),
    ]:
        corr, pval = compute_correlation_matrix(df, method)
        fig = plot_correlation_heatmap(corr, title=f"Correlación {label}")
        sections.append(f'<h3>Correlación {label}</h3>')
        sections.append(f'<div class="chart-container-full"><img src="data:image/png;base64,{_fig_to_base64(fig)}"></div>')
    
    # 2. Seasonal correlations
    logger.info("Computing seasonal correlations...")
    seasonal = seasonal_correlation(df_daily)
    fig_s = plot_seasonal_heatmaps(seasonal)
    sections.append(f'<h3>Correlación Estacional</h3>')
    sections.append(f'<div class="chart-container-full"><img src="data:image/png;base64,{_fig_to_base64(fig_s)}"></div>')
    
    # 3. Cross-correlations with lag
    logger.info("Computing cross-correlations...")
    pairs = [("t2m", "swvl1"), ("t2m", "pev"), ("swvl1", "pev")]
    for vx, vy in pairs:
        lags, cc = cross_correlation_with_lag(df_hourly, vx, vy, max_lag_hours=48)
        fig_cc = plot_cross_correlation(lags, cc, vx, vy)
        sections.append(f'<div class="chart-container-full"><img src="data:image/png;base64,{_fig_to_base64(fig_cc)}"></div>')
    
    # 4. PCA
    logger.info("Running PCA...")
    pca_res = pca_analysis(df_daily)
    fig_pca = plot_pca_biplot(pca_res, df_daily)
    sections.append(f'<h3>Análisis de Componentes Principales (PCA)</h3>')
    sections.append(f'<div class="chart-container-full"><img src="data:image/png;base64,{_fig_to_base64(fig_pca)}"></div>')
    
    # 5. Annual trends
    logger.info("Computing annual trends...")
    annual, trends = compute_annual_trends(df_daily)
    fig_t = plot_annual_trends(annual, trends)
    sections.append(f'<h3>Tendencias Anuales (Mann-Kendall)</h3>')
    sections.append(f'<div class="chart-container-full"><img src="data:image/png;base64,{_fig_to_base64(fig_t)}"></div>')
    
    # Build trend summary table
    trend_rows = ""
    for var, t in trends.items():
        sig = "✅" if t["significant"] else "❌"
        trend_rows += f"<tr><td>{VAR_META[var]['label']}</td><td>{t['slope_per_year']:+.5f}</td><td>{t['r_squared']:.4f}</td><td>{t['p_value']:.4f}</td><td>{sig}</td></tr>"
    
    sections.append(f"""
    <h3>Resumen de Tendencias</h3>
    <table class="scientific-table">
        <tr><th>Variable</th><th>Pendiente/año</th><th>R²</th><th>p-value</th><th>Significativa (α=0.05)</th></tr>
        {trend_rows}
    </table>
    """)
    
    html = f"""
    <div class="scientific-report">
        <style>
            .scientific-report {{ font-family: 'Inter', sans-serif; color: #f1f5f9; padding: 20px; }}
            .scientific-report h2 {{ color: #38bdf8; font-size: 1.5rem; }}
            .scientific-report h3 {{ color: #7dd3fc; border-left: 5px solid #38bdf8; padding-left: 15px; margin-top: 50px; text-transform: uppercase; }}
            .scientific-table {{ width: 100%; border-collapse: collapse; font-size: 0.8rem; background: #0f172a; }}
            .scientific-table th {{ background: #334155; color: #38bdf8; padding: 10px; border: 1px solid #475569; }}
            .scientific-table td {{ padding: 8px; border: 1px solid #334155; text-align: center; }}
            .chart-container-full {{ background: white; padding: 20px; border-radius: 12px; margin: 20px 0; text-align: center; }}
            .chart-container-full img {{ width: 100%; height: auto; display: block; }}
        </style>
        <h2>Análisis de Correlación Multivariante — Cuenca del Tamesí</h2>
        <p style="color:#94a3b8; font-style:italic;">ERA5-Land 1998–2025 | t2m, swvl1, pev | Autor: Raul A. Morales Rivera</p>
        {''.join(sections)}
    </div>
    """
    return html


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    html = generate_correlation_html_report()
    out = Path("reports") / "correlation_report.html"
    out.parent.mkdir(exist_ok=True)
    with open(out, "w", encoding="utf-8") as f:
        f.write(f"<html><head><meta charset='utf-8'><title>Correlation Report</title></head><body style='background:#0f172a'>{html}</body></html>")
    logger.info(f"Report saved to {out}")
