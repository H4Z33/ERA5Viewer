"""
Validation Module for CHSI against documented extreme events in the Tamesí Basin.
Compares CHSI time series against known droughts, floods, and hurricanes
to evaluate its utility as a hydric stress proxy.

Author: Raul Alejandro Morales Rivera, DCI, Posgrado FIT
"""

import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import seaborn as sns
from scipy import stats
from sklearn.metrics import roc_auc_score, precision_recall_curve, f1_score
import io
import base64
import warnings
import logging
from pathlib import Path

warnings.filterwarnings('ignore')
logger = logging.getLogger("validation")

# ============================================================
# Documented Extreme Events Catalog — Cuenca Tamesí / Tamaulipas Sur
# Sources: CONAGUA, FloodList, WMO, CENAPRED, Columbia/IRI
# ============================================================

EXTREME_EVENTS = [
    # Droughts (CHSI should be HIGH)
    {"start": "1998-01-01", "end": "2003-12-31", "type": "drought", "severity": "moderate",
     "name": "Sequía multinanual norte de México 1998-2003",
     "description": "Sequía persistente afectando norte de México incluyendo Tamaulipas"},
    {"start": "2011-01-01", "end": "2012-06-30", "type": "drought", "severity": "extreme",
     "name": "Sequía excepcional 2011-2012",
     "description": "Una de las peores sequías registradas en el norte de México. Pérdidas agrícolas masivas."},
    {"start": "2022-03-01", "end": "2022-09-30", "type": "drought", "severity": "severe",
     "name": "Sequía severa 2022",
     "description": "Sequía severa a extrema en Tamaulipas, restricciones de agua."},
    {"start": "2024-03-01", "end": "2024-09-30", "type": "drought", "severity": "exceptional",
     "name": "Sequía excepcional 2024",
     "description": "La peor sequía registrada en sur de Tamaulipas. Restricciones industriales en Altamira."},

    # Wet/Flood Events (CHSI should be LOW)
    {"start": "2000-10-01", "end": "2000-10-15", "type": "flood", "severity": "moderate",
     "name": "Huracán Keith 2000",
     "description": "Cat. 1 hurricane near Tampico. Heavy rainfall and flooding."},
    {"start": "2007-07-01", "end": "2007-07-31", "type": "flood", "severity": "severe",
     "name": "Inundaciones Julio 2007",
     "description": "Lluvias torrenciales en la cuenca del Tamesí"},
    {"start": "2010-06-15", "end": "2010-07-15", "type": "flood", "severity": "extreme",
     "name": "Huracán Alex 2010",
     "description": "Precipitación extrema asociada al Huracán Alex. Inundaciones severas."},
    {"start": "2013-09-15", "end": "2013-10-15", "type": "flood", "severity": "extreme",
     "name": "Huracán Ingrid 2013",
     "description": "Doble impacto Ingrid (Golfo) + Manuel (Pacífico). Inundaciones severas."},
    {"start": "2017-09-20", "end": "2017-10-10", "type": "flood", "severity": "severe",
     "name": "Inundaciones Sept-Oct 2017",
     "description": "Desbordamiento del río Corona. 40+ comunidades afectadas. 245mm en Altamira."},
]


def load_chsi(csv_path=None):
    """Load the pre-computed CHSI time series."""
    if csv_path is None:
        csv_path = Path("reports") / "chsi_tamesi_1998_2025.csv"
    df = pd.read_csv(csv_path, index_col=0, parse_dates=True)
    df.columns = ["CHSI"]
    return df


def compute_event_statistics(chsi_df, events=EXTREME_EVENTS):
    """
    For each documented event, compute CHSI statistics during the event
    and compare against the non-event baseline.
    """
    results = []
    
    # Baseline: all non-event periods
    event_mask = pd.Series(False, index=chsi_df.index)
    for ev in events:
        mask = (chsi_df.index >= ev["start"]) & (chsi_df.index <= ev["end"])
        event_mask = event_mask | mask
    
    baseline_chsi = chsi_df.loc[~event_mask, "CHSI"]
    baseline_mean = baseline_chsi.mean()
    baseline_std = baseline_chsi.std()
    
    for ev in events:
        mask = (chsi_df.index >= ev["start"]) & (chsi_df.index <= ev["end"])
        event_data = chsi_df.loc[mask, "CHSI"]
        
        if len(event_data) == 0:
            continue
        
        ev_mean = event_data.mean()
        ev_std = event_data.std()
        ev_max = event_data.max()
        ev_min = event_data.min()
        
        # Z-score relative to baseline
        z_score = (ev_mean - baseline_mean) / baseline_std
        
        # Expected direction
        if ev["type"] == "drought":
            correct_direction = ev_mean > baseline_mean
            expected = "ALTO (estrés)"
        else:
            correct_direction = ev_mean < baseline_mean
            expected = "BAJO (húmedo)"
        
        results.append({
            "Evento": ev["name"],
            "Tipo": ev["type"],
            "Severidad": ev["severity"],
            "Periodo": f"{ev['start']} → {ev['end']}",
            "CHSI_mean": round(ev_mean, 4),
            "CHSI_max": round(ev_max, 4),
            "CHSI_min": round(ev_min, 4),
            "Baseline_mean": round(baseline_mean, 4),
            "Z_score": round(z_score, 3),
            "Esperado": expected,
            "Dirección_correcta": "✅" if correct_direction else "❌",
            "n_days": len(event_data),
        })
    
    return pd.DataFrame(results), baseline_mean, baseline_std


def compute_binary_classification_metrics(chsi_df, events=EXTREME_EVENTS, 
                                           percentile_threshold=75):
    """
    Evaluate CHSI as a binary drought detector.
    Label days in drought events as positive, everything else as negative.
    Use CHSI percentile as threshold.
    """
    # Create binary labels
    labels = pd.Series(0, index=chsi_df.index, name="is_drought")
    for ev in events:
        if ev["type"] == "drought":
            mask = (chsi_df.index >= ev["start"]) & (chsi_df.index <= ev["end"])
            labels[mask] = 1
    
    # CHSI prediction: high CHSI = drought
    threshold = np.percentile(chsi_df["CHSI"], percentile_threshold)
    predictions = (chsi_df["CHSI"] >= threshold).astype(int)
    
    # Align
    common = labels.index.intersection(chsi_df.index)
    y_true = labels[common].values
    y_score = chsi_df.loc[common, "CHSI"].values
    y_pred = predictions[common].values
    
    # Metrics
    if len(np.unique(y_true)) < 2:
        return {"error": "Not enough positive samples for classification metrics"}
    
    auc = roc_auc_score(y_true, y_score)
    precision, recall, _ = precision_recall_curve(y_true, y_score)
    f1 = f1_score(y_true, y_pred)
    
    return {
        "auc_roc": round(auc, 4),
        "f1_score": round(f1, 4),
        "threshold": round(threshold, 4),
        "n_drought_days": int(y_true.sum()),
        "n_total_days": len(y_true),
        "prevalence": round(y_true.mean(), 4),
        "precision_curve": precision,
        "recall_curve": recall,
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


def plot_chsi_with_events(chsi_df, events=EXTREME_EVENTS):
    """Plot CHSI time series with event annotations."""
    fig, ax = plt.subplots(figsize=(18, 7))
    
    # CHSI rolling mean
    rolling = chsi_df["CHSI"].rolling(30).mean()
    ax.plot(chsi_df.index, chsi_df["CHSI"], color="#94a3b8", alpha=0.3, linewidth=0.5)
    ax.plot(rolling.index, rolling.values, color="#38bdf8", linewidth=1.5, label="CHSI (30d avg)")
    
    # Event shading
    drought_color = "#ef4444"
    flood_color = "#22c55e"
    
    for ev in events:
        start = pd.Timestamp(ev["start"])
        end = pd.Timestamp(ev["end"])
        color = drought_color if ev["type"] == "drought" else flood_color
        alpha = {"moderate": 0.15, "severe": 0.25, "extreme": 0.35, "exceptional": 0.45}.get(ev["severity"], 0.2)
        ax.axvspan(start, end, alpha=alpha, color=color, zorder=0)
        
        # Label
        mid = start + (end - start) / 2
        y_pos = 0.92 if ev["type"] == "drought" else 0.08
        ax.text(mid, y_pos, ev["name"], ha='center', va='center', fontsize=6,
                rotation=90, color=color, fontweight='bold', alpha=0.8,
                transform=ax.get_xaxis_transform())
    
    # Legend patches
    from matplotlib.patches import Patch
    legend_elements = [
        Patch(facecolor=drought_color, alpha=0.3, label='Sequía documentada'),
        Patch(facecolor=flood_color, alpha=0.3, label='Inundación documentada'),
        plt.Line2D([0], [0], color='#38bdf8', linewidth=2, label='CHSI (30d avg)'),
    ]
    ax.legend(handles=legend_elements, loc='upper left', fontsize=9)
    
    ax.set_ylabel("CHSI (0 = sin estrés, 1 = estrés máximo)", fontsize=10)
    ax.set_title("CHSI vs. Eventos Extremos Documentados — Cuenca del Tamesí (1998–2025)", 
                 fontsize=14, fontweight='bold')
    ax.set_ylim(0, 1)
    ax.grid(True, alpha=0.2)
    ax.xaxis.set_major_locator(mdates.YearLocator(2))
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
    plt.xticks(rotation=45)
    plt.tight_layout()
    return fig


def plot_event_comparison_boxplot(chsi_df, events=EXTREME_EVENTS):
    """Boxplot comparing CHSI distributions: drought vs flood vs baseline."""
    categories = []
    values = []
    
    event_mask = pd.Series(False, index=chsi_df.index)
    
    for ev in events:
        mask = (chsi_df.index >= ev["start"]) & (chsi_df.index <= ev["end"])
        event_mask = event_mask | mask
        event_chsi = chsi_df.loc[mask, "CHSI"]
        label = f"{'🔴' if ev['type'] == 'drought' else '🟢'} {ev['name'][:30]}"
        for v in event_chsi.values:
            categories.append(label)
            values.append(v)
    
    # Add baseline
    baseline = chsi_df.loc[~event_mask, "CHSI"]
    for v in baseline.sample(min(2000, len(baseline)), random_state=42).values:
        categories.append("⬜ Baseline (sin evento)")
        values.append(v)
    
    df_plot = pd.DataFrame({"Periodo": categories, "CHSI": values})
    
    fig, ax = plt.subplots(figsize=(14, 10))
    order = sorted(df_plot["Periodo"].unique(), key=lambda x: df_plot[df_plot["Periodo"]==x]["CHSI"].mean(), reverse=True)
    sns.boxplot(data=df_plot, y="Periodo", x="CHSI", orient="h", order=order, ax=ax, 
                palette="RdYlGn_r", width=0.6)
    ax.set_xlabel("CHSI")
    ax.set_title("Distribución del CHSI por Evento vs Baseline", fontsize=14, fontweight='bold')
    ax.grid(True, alpha=0.3, axis='x')
    plt.tight_layout()
    return fig


def plot_precision_recall(metrics):
    """Plot precision-recall curve for drought detection."""
    fig, ax = plt.subplots(figsize=(8, 6))
    ax.plot(metrics["recall_curve"], metrics["precision_curve"], color="#38bdf8", linewidth=2)
    ax.fill_between(metrics["recall_curve"], metrics["precision_curve"], alpha=0.1, color="#38bdf8")
    ax.set_xlabel("Recall (Sensibilidad)")
    ax.set_ylabel("Precision (Precisión)")
    ax.set_title(f"Curva Precision-Recall — AUC-ROC={metrics['auc_roc']:.4f}", fontsize=13, fontweight='bold')
    ax.grid(True, alpha=0.3)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    plt.tight_layout()
    return fig


# ============================================================
# HTML Report
# ============================================================

def generate_validation_html_report():
    """Generate full validation HTML report."""
    logger.info("Loading CHSI data...")
    chsi_df = load_chsi()
    
    sections = []
    
    # 1. CHSI vs Events timeline
    logger.info("Plotting CHSI vs events...")
    fig1 = plot_chsi_with_events(chsi_df)
    sections.append('<h3>1. CHSI vs Eventos Extremos Documentados</h3>')
    sections.append(f'<div class="chart-container-full"><img src="data:image/png;base64,{_fig_to_base64(fig1)}"></div>')
    
    # 2. Event statistics table
    logger.info("Computing event statistics...")
    ev_df, bl_mean, bl_std = compute_event_statistics(chsi_df)
    
    # Summary stats
    n_correct = (ev_df["Dirección_correcta"] == "✅").sum()
    n_total = len(ev_df)
    accuracy = n_correct / n_total * 100
    
    sections.append(f'<h3>2. Estadísticas por Evento</h3>')
    sections.append(f'<p style="color:#94a3b8">Baseline CHSI: μ={bl_mean:.4f}, σ={bl_std:.4f} | Concordancia direccional: <strong>{n_correct}/{n_total} ({accuracy:.0f}%)</strong></p>')
    
    ev_html = ev_df.to_html(classes="scientific-table", index=False)
    sections.append(f'<div style="overflow-x:auto">{ev_html}</div>')
    
    # 3. Boxplot comparison
    logger.info("Generating comparison boxplot...")
    fig2 = plot_event_comparison_boxplot(chsi_df)
    sections.append(f'<h3>3. Distribución CHSI: Eventos vs Baseline</h3>')
    sections.append(f'<div class="chart-container-full"><img src="data:image/png;base64,{_fig_to_base64(fig2)}"></div>')
    
    # 4. Binary classification metrics
    logger.info("Computing classification metrics...")
    metrics = compute_binary_classification_metrics(chsi_df)
    if "error" not in metrics:
        fig3 = plot_precision_recall(metrics)
        sections.append(f'<h3>4. CHSI como Detector de Sequía</h3>')
        sections.append(f"""
        <div class="metrics-grid">
            <div class="metric-card"><span class="metric-value">{metrics['auc_roc']}</span><span class="metric-label">AUC-ROC</span></div>
            <div class="metric-card"><span class="metric-value">{metrics['f1_score']}</span><span class="metric-label">F1 Score</span></div>
            <div class="metric-card"><span class="metric-value">{metrics['n_drought_days']}</span><span class="metric-label">Días de sequía</span></div>
            <div class="metric-card"><span class="metric-value">{metrics['prevalence']:.1%}</span><span class="metric-label">Prevalencia</span></div>
        </div>
        """)
        sections.append(f'<div class="chart-container-full"><img src="data:image/png;base64,{_fig_to_base64(fig3)}"></div>')
    
    html = f"""
    <div class="scientific-report">
        <style>
            .scientific-report {{ font-family: 'Inter', sans-serif; color: #f1f5f9; padding: 20px; }}
            .scientific-report h2 {{ color: #38bdf8; font-size: 1.5rem; }}
            .scientific-report h3 {{ color: #7dd3fc; border-left: 5px solid #38bdf8; padding-left: 15px; margin-top: 50px; text-transform: uppercase; }}
            .scientific-table {{ width: 100%; border-collapse: collapse; font-size: 0.7rem; background: #0f172a; }}
            .scientific-table th {{ background: #334155; color: #38bdf8; padding: 8px; border: 1px solid #475569; }}
            .scientific-table td {{ padding: 6px; border: 1px solid #334155; text-align: center; }}
            .chart-container-full {{ background: white; padding: 20px; border-radius: 12px; margin: 20px 0; text-align: center; }}
            .chart-container-full img {{ width: 100%; height: auto; display: block; }}
            .metrics-grid {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 15px; margin: 20px 0; }}
            .metric-card {{ background: rgba(56,189,248,0.1); border: 1px solid #334155; border-radius: 12px; padding: 20px; text-align: center; }}
            .metric-value {{ display: block; font-size: 1.8rem; font-weight: bold; color: #38bdf8; }}
            .metric-label {{ display: block; font-size: 0.8rem; color: #94a3b8; margin-top: 5px; }}
        </style>
        <h2>Validación del CHSI — Eventos Extremos Documentados</h2>
        <p style="color:#94a3b8; font-style:italic;">Cuenca del Río Tamesí | 1998–2025 | Autor: Raul A. Morales Rivera</p>
        {''.join(sections)}
    </div>
    """
    return html


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    html = generate_validation_html_report()
    out = Path("reports") / "validation_report.html"
    out.parent.mkdir(exist_ok=True)
    with open(out, "w", encoding="utf-8") as f:
        f.write(f"<html><head><meta charset='utf-8'><title>Validation Report</title></head><body style='background:#0f172a'>{html}</body></html>")
    logger.info(f"Validation report saved to {out}")
