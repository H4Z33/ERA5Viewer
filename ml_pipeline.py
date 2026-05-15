"""
Machine Learning Pipeline for Composite Hydric Stress Index (CHSI) Derivation.
Trains RF/XGBoost models on ERA5-Land variables (t2m, swvl1, pev) to derive
a composite index that captures integrated hydric stress dynamics.

Author: Raul Alejandro Morales Rivera, DCI, Posgrado FIT
"""

import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.preprocessing import StandardScaler, MinMaxScaler
from sklearn.model_selection import TimeSeriesSplit
from sklearn.metrics import mean_squared_error, r2_score, mean_absolute_error
from sklearn.decomposition import PCA
import io
import base64
import warnings
import logging
from pathlib import Path

warnings.filterwarnings('ignore')
logger = logging.getLogger("ml_pipeline")

from correlation_analysis import load_multivariate_df, VAR_META, compute_anomalies


# ============================================================
# Feature Engineering
# ============================================================

def engineer_features(df, window_days=7):
    """
    Create derived features from the three base variables.
    This captures temporal dynamics, ratios, and stress indicators.
    """
    feat = df[["t2m", "swvl1", "pev"]].copy()
    
    # 1. Physical ratios
    feat["pev_swvl1_ratio"] = feat["pev"].abs() / (feat["swvl1"] + 1e-6)
    feat["thermal_moisture_index"] = feat["t2m"] / (feat["swvl1"] + 1e-6)
    
    # 2. Rolling statistics (window_days)
    w = window_days * 24  # convert to hours
    for col in ["t2m", "swvl1", "pev"]:
        feat[f"{col}_roll_mean_{window_days}d"] = feat[col].rolling(w, min_periods=1).mean()
        feat[f"{col}_roll_std_{window_days}d"] = feat[col].rolling(w, min_periods=1).std()
    
    # 3. Temporal derivatives (rate of change)
    for col in ["t2m", "swvl1", "pev"]:
        feat[f"{col}_diff_1h"] = feat[col].diff(1)
        feat[f"{col}_diff_24h"] = feat[col].diff(24)
    
    # 4. Anomalies (departure from monthly climatology)
    anomalies = compute_anomalies(df[["t2m", "swvl1", "pev"]])
    for col in ["t2m", "swvl1", "pev"]:
        feat[f"{col}_anomaly"] = anomalies[col]
    
    # 5. Cyclical time encoding
    feat["hour_sin"] = np.sin(2 * np.pi * df.index.hour / 24)
    feat["hour_cos"] = np.cos(2 * np.pi * df.index.hour / 24)
    feat["month_sin"] = np.sin(2 * np.pi * df.index.month / 12)
    feat["month_cos"] = np.cos(2 * np.pi * df.index.month / 12)
    feat["doy_sin"] = np.sin(2 * np.pi * df.index.dayofyear / 365.25)
    feat["doy_cos"] = np.cos(2 * np.pi * df.index.dayofyear / 365.25)
    
    feat.dropna(inplace=True)
    return feat


def create_stress_target(df):
    """
    Create a proxy stress target variable using physically-informed combination.
    
    The CHSI target is based on the water balance principle:
    - High temperature → high atmospheric demand → stress ↑
    - Low soil moisture → limited water supply → stress ↑  
    - High potential evaporation magnitude → stress ↑
    
    We normalize each component and combine them as:
    CHSI = w1 * norm(t2m) + w2 * (1 - norm(swvl1)) + w3 * norm(|pev|)
    """
    scaler = MinMaxScaler()
    
    # Use daily means to reduce noise
    daily = df[["t2m", "swvl1", "pev"]].resample("1D").mean().dropna()
    
    t2m_n = scaler.fit_transform(daily[["t2m"]])[:, 0]
    swvl1_n = scaler.fit_transform(daily[["swvl1"]])[:, 0]
    pev_n = scaler.fit_transform(daily[["pev"]].abs())[:, 0]
    
    # Equal weighting — the ML model will learn the optimal combination
    chsi = (t2m_n + (1 - swvl1_n) + pev_n) / 3.0
    
    daily["CHSI_target"] = chsi
    return daily


def train_chsi_model(df, model_type="rf", n_splits=5):
    """
    Train a ML model to predict CHSI from engineered features.
    Uses time-series cross-validation to prevent leakage.
    """
    # Create target on daily data
    daily_target = create_stress_target(df)
    
    # Engineer features on daily data
    df_daily = df.resample("1D").mean().dropna()
    features = engineer_features(df_daily, window_days=7)
    
    # Align
    common_idx = features.index.intersection(daily_target.index)
    X = features.loc[common_idx]
    y = daily_target.loc[common_idx, "CHSI_target"]
    
    # Remove base variables from features (we want derived features only)
    feature_cols = [c for c in X.columns if c not in ["t2m", "swvl1", "pev"]]
    X = X[feature_cols]
    
    # Model selection
    if model_type == "rf":
        model = RandomForestRegressor(
            n_estimators=200, max_depth=15, min_samples_leaf=10,
            random_state=42, n_jobs=-1
        )
    else:
        model = GradientBoostingRegressor(
            n_estimators=200, max_depth=8, learning_rate=0.05,
            subsample=0.8, random_state=42
        )
    
    # Time-series cross-validation
    tscv = TimeSeriesSplit(n_splits=n_splits)
    cv_results = []
    
    for fold, (train_idx, test_idx) in enumerate(tscv.split(X)):
        X_train, X_test = X.iloc[train_idx], X.iloc[test_idx]
        y_train, y_test = y.iloc[train_idx], y.iloc[test_idx]
        
        model.fit(X_train, y_train)
        y_pred = model.predict(X_test)
        
        cv_results.append({
            "fold": fold + 1,
            "rmse": np.sqrt(mean_squared_error(y_test, y_pred)),
            "mae": mean_absolute_error(y_test, y_pred),
            "r2": r2_score(y_test, y_pred),
            "test_start": X_test.index[0],
            "test_end": X_test.index[-1],
        })
    
    # Final model on all data
    model.fit(X, y)
    y_pred_full = model.predict(X)
    
    # Feature importance
    importances = pd.Series(model.feature_importances_, index=feature_cols).sort_values(ascending=False)
    
    # Build CHSI series
    chsi_series = pd.Series(y_pred_full, index=common_idx, name="CHSI")
    
    return {
        "model": model,
        "cv_results": pd.DataFrame(cv_results),
        "feature_importance": importances,
        "chsi_series": chsi_series,
        "chsi_target": y,
        "feature_names": feature_cols,
        "X": X,
    }


# ============================================================
# Visualization
# ============================================================

def _fig_to_base64(fig):
    buf = io.BytesIO()
    fig.savefig(buf, format='png', dpi=140, bbox_inches='tight')
    buf.seek(0)
    img_str = base64.b64encode(buf.read()).decode('utf-8')
    plt.close(fig)
    return img_str


def plot_feature_importance(importances, top_n=15):
    """Plot top feature importances."""
    fig, ax = plt.subplots(figsize=(12, 7))
    top = importances.head(top_n)
    colors = plt.cm.viridis(np.linspace(0.3, 0.9, len(top)))
    top.plot(kind='barh', ax=ax, color=colors)
    ax.set_xlabel("Importancia (Gini)")
    ax.set_title(f"Top {top_n} Features — Modelo CHSI", fontsize=14, fontweight='bold')
    ax.invert_yaxis()
    ax.grid(True, alpha=0.3, axis='x')
    plt.tight_layout()
    return fig


def plot_chsi_timeseries(chsi_series, target=None):
    """Plot the CHSI time series with optional target overlay."""
    fig, ax = plt.subplots(figsize=(16, 6))
    
    if target is not None:
        ax.fill_between(target.index, 0, target.values, alpha=0.2, color="#94a3b8", label="Target (físico)")
    
    ax.plot(chsi_series.index, chsi_series.values, color="#ef4444", linewidth=0.8, alpha=0.9, label="CHSI (ML)")
    
    # Rolling mean for clarity
    rolling = chsi_series.rolling(30).mean()
    ax.plot(rolling.index, rolling.values, color="#38bdf8", linewidth=2, label="CHSI (media móvil 30d)")
    
    ax.set_ylabel("CHSI (0 = sin estrés, 1 = estrés máximo)")
    ax.set_xlabel("Fecha")
    ax.set_title("Índice Compuesto de Estrés Hídrico (CHSI) — Cuenca del Tamesí", fontsize=14, fontweight='bold')
    ax.legend(loc='upper right')
    ax.set_ylim(0, 1)
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    return fig


def plot_cv_results(cv_df):
    """Plot cross-validation metrics per fold."""
    fig, axes = plt.subplots(1, 3, figsize=(15, 5))
    metrics = ["rmse", "mae", "r2"]
    colors = ["#ef4444", "#f59e0b", "#22c55e"]
    titles = ["RMSE", "MAE", "R²"]
    
    for ax, metric, color, title in zip(axes, metrics, colors, titles):
        ax.bar(cv_df["fold"], cv_df[metric], color=color, alpha=0.8)
        mean_val = cv_df[metric].mean()
        ax.axhline(mean_val, color='gray', linestyle='--', linewidth=1)
        ax.set_title(f"{title} (μ={mean_val:.4f})", fontweight='bold')
        ax.set_xlabel("Fold")
        ax.set_ylabel(title)
        ax.grid(True, alpha=0.3, axis='y')
    
    fig.suptitle("Validación Cruzada Temporal (TimeSeriesSplit)", fontsize=14, fontweight='bold', y=1.02)
    plt.tight_layout()
    return fig


def plot_chsi_annual_boxplot(chsi_series):
    """Annual boxplot of CHSI distribution."""
    fig, ax = plt.subplots(figsize=(14, 6))
    df_box = pd.DataFrame({"CHSI": chsi_series.values, "Año": chsi_series.index.year})
    sns.boxplot(data=df_box, x="Año", y="CHSI", color="#818cf8", ax=ax)
    ax.set_title("Distribución Anual del CHSI", fontsize=14, fontweight='bold')
    plt.xticks(rotation=90)
    ax.grid(True, alpha=0.3, axis='y')
    plt.tight_layout()
    return fig


# ============================================================
# Full Report Generator
# ============================================================

def generate_chsi_html_report(model_type="rf"):
    """Generate a complete CHSI analysis HTML report."""
    logger.info("Loading data...")
    df = load_multivariate_df()
    
    logger.info(f"Training {model_type.upper()} model...")
    results = train_chsi_model(df, model_type=model_type)
    
    sections = []
    
    # 1. CV Results
    fig_cv = plot_cv_results(results["cv_results"])
    sections.append(f'<h3>1. Validación Cruzada Temporal</h3>')
    sections.append(f'<div class="chart-container-full"><img src="data:image/png;base64,{_fig_to_base64(fig_cv)}"></div>')
    
    cv_html = results["cv_results"].round(4).to_html(classes="scientific-table", index=False)
    sections.append(f'<div style="overflow-x:auto">{cv_html}</div>')
    
    # 2. Feature Importance
    fig_fi = plot_feature_importance(results["feature_importance"])
    sections.append(f'<h3>2. Importancia de Features</h3>')
    sections.append(f'<div class="chart-container-full"><img src="data:image/png;base64,{_fig_to_base64(fig_fi)}"></div>')
    
    # 3. CHSI Time Series
    fig_ts = plot_chsi_timeseries(results["chsi_series"], results["chsi_target"])
    sections.append(f'<h3>3. Serie Temporal del CHSI</h3>')
    sections.append(f'<div class="chart-container-full"><img src="data:image/png;base64,{_fig_to_base64(fig_ts)}"></div>')
    
    # 4. Annual boxplot
    fig_ab = plot_chsi_annual_boxplot(results["chsi_series"])
    sections.append(f'<h3>4. Distribución Anual del CHSI</h3>')
    sections.append(f'<div class="chart-container-full"><img src="data:image/png;base64,{_fig_to_base64(fig_ab)}"></div>')
    
    # 5. Export CHSI as CSV
    csv_path = Path("reports") / "chsi_tamesi_1998_2025.csv"
    csv_path.parent.mkdir(exist_ok=True)
    results["chsi_series"].to_csv(csv_path, header=True)
    sections.append(f'<h3>5. Dataset Exportado</h3>')
    sections.append(f'<p style="color:#94a3b8">CHSI series exportada a: <code>{csv_path.absolute()}</code></p>')
    
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
        <h2>CHSI — Composite Hydric Stress Index</h2>
        <p style="color:#94a3b8; font-style:italic;">Cuenca del Río Tamesí | ERA5-Land 1998–2025 | Modelo: {model_type.upper()}</p>
        <p style="color:#94a3b8; font-style:italic;">Autor: Raul A. Morales Rivera, DCI, Posgrado FIT</p>
        {''.join(sections)}
    </div>
    """
    return html, results


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    html, results = generate_chsi_html_report("rf")
    out = Path("reports") / "chsi_report.html"
    with open(out, "w", encoding="utf-8") as f:
        f.write(f"<html><head><meta charset='utf-8'><title>CHSI Report</title></head><body style='background:#0f172a'>{html}</body></html>")
    logger.info(f"CHSI report saved to {out}")
    logger.info(f"CV Summary:\n{results['cv_results'].to_string()}")
