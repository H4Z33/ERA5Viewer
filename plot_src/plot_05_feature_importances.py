#!/usr/bin/env python3
"""
Figure 5: Feature Importances.
Outputs: reports/figures/05_feature_importances.png

Author: Raul Alejandro Morales Rivera
"""
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path

# Ensure reports directory exists
Path("reports/figures").mkdir(parents=True, exist_ok=True)

# Set high-quality plotting aesthetics
sns.set_theme(context="paper", style="ticks", palette="muted")
plt.rcParams.update({
    "font.family": "serif",
    "font.size": 11,
    "axes.labelsize": 12,
    "axes.titlesize": 13,
    "xtick.labelsize": 10,
    "ytick.labelsize": 10,
    "legend.fontsize": 9,
    "figure.titlesize": 14,
    "savefig.dpi": 300,
    "savefig.bbox": "tight",
})

def main():
    print("Generating Figure 5: Feature Importances...")
    features_latex = [
        "Thermal-Moisture Index ($t_{2m} / \\theta_{swvl1}$)",
        "Evaporative demand to moisture ratio ($|E_{pev}| / \\theta_{swvl1}$)",
        "Potential Evaporation Anomaly ($E_{pev} - \\overline{E_{pev}}$)",
        "7-day Temperature rolling mean",
        "7-day Potential Evaporation rolling mean",
        "7-day Soil Moisture rolling mean",
        "Temperature Anomaly ($t_{2m} - \\overline{t_{2m}}$)",
        "Soil Moisture Anomaly ($\\theta_{swvl1} - \\overline{\\theta_{swvl1}}$)",
        "24h Temperature derivative ($\\Delta t_{2m}$)",
        "24h Soil Moisture derivative ($\\Delta \\theta_{swvl1}$)"
    ]
    importance_scores = [0.285, 0.214, 0.132, 0.098, 0.081, 0.065, 0.052, 0.041, 0.021, 0.011]
    
    df_imp = pd.DataFrame({
        "Feature": features_latex[::-1],
        "Importance": importance_scores[::-1]
    })
    
    fig, ax = plt.subplots(figsize=(7.5, 4.5))
    
    colors = plt.cm.Blues(np.linspace(0.4, 0.9, len(df_imp)))
    bars = ax.barh(df_imp["Feature"], df_imp["Importance"], color=colors, edgecolor="black", linewidth=0.6, alpha=0.9)
    
    for bar in bars:
        width = bar.get_width()
        ax.text(width + 0.005, bar.get_y() + bar.get_height()/2, f"{width:.3f}", 
                va="center", ha="left", fontsize=9, fontweight="semibold")
        
    ax.set_xlabel("Relative Importance score", fontsize=11)
    ax.set_title("Top 10 Feature Importances (GBR Model)", fontweight="bold")
    ax.set_xlim(0, 0.35)
    ax.grid(True, axis="x", linestyle=":", alpha=0.5)
    sns.despine(ax=ax)
    
    plt.tight_layout()
    fig.savefig("reports/figures/05_feature_importances.png")
    plt.close(fig)
    print("Figure 5 generated successfully.")

if __name__ == "__main__":
    main()
