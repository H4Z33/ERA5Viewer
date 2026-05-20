#!/usr/bin/env python3
"""
Figure 2: Seasonal Correlation heatmaps.
Outputs: reports/figures/02_seasonal_correlation.png

Author: Raul Alejandro Morales Rivera
"""
import sqlite3
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

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

DB_PATH = Path("era5_stats.db")

def load_data():
    if not DB_PATH.exists():
        raise FileNotFoundError("era5_stats.db not found.")
    
    with sqlite3.connect(DB_PATH) as conn:
        df_raw = pd.read_sql_query("SELECT variable, time_str, mean FROM hourly_stats", conn)
    
    df = df_raw.pivot(index="time_str", columns="variable", values="mean")
    df.index = pd.to_datetime(df.index)
    df.sort_index(inplace=True)
    
    # Conversions
    if "t2m" in df.columns:
        df["t2m"] = df["t2m"] - 273.15
    return df.dropna()

def main():
    print("Loading data...")
    df = load_data()
    
    print("Generating Figure 2: Seasonal Correlation...")
    daily = df.resample("1D").mean()
    
    seasons = {
        "DJF (Winter)": [12, 1, 2],
        "MAM (Spring)": [3, 4, 5],
        "JJA (Summer)":    [6, 7, 8],
        "SON (Autumn)":     [9, 10, 11]
    }
    
    fig, axes = plt.subplots(2, 2, figsize=(9.5, 8.5))
    axes = axes.flatten()
    
    var_labels = ["$t_{2m}$", "$\\theta_{swvl1}$", "$E_{pev}$"]
    
    for i, (name, months) in enumerate(seasons.items()):
        ax = axes[i]
        mask = daily.index.month.isin(months)
        corr_matrix = daily[mask][["t2m", "swvl1", "pev"]].corr()
        
        sns.heatmap(
            corr_matrix, annot=True, fmt=".3f", cmap="RdBu_r", center=0,
            vmin=-1, vmax=1, ax=ax, xticklabels=var_labels, yticklabels=var_labels,
            linewidths=0.5, square=True, cbar_kws={"shrink": 0.7}
        )
        ax.set_title(f"Season: {name}", fontweight="bold", fontsize=11)
        
    plt.suptitle("Meteorological Seasonal Correlation Analysis", fontsize=13, fontweight="bold", y=0.98)
    plt.tight_layout()
    fig.savefig("reports/figures/02_seasonal_correlation.png")
    plt.close(fig)
    print("Figure 2 generated successfully.")

if __name__ == "__main__":
    main()
