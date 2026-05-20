#!/usr/bin/env python3
"""
Figure 1: Long-term Climatic Trends (t2m, swvl1, pev).
Outputs: reports/figures/01_climatic_trends.png

Author: Raul Alejandro Morales Rivera
"""
import sqlite3
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats

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
        raise FileNotFoundError("era5_stats.db not found. Run preprocess.py first.")
    
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
    
    print("Generating Figure 1: Climatic Trends...")
    annual = df.resample("YE").mean()
    
    fig, axes = plt.subplots(3, 1, figsize=(8.5, 9.5), sharex=True)
    variables = [
        ("t2m", "Temperature ($t_{2m}$)", "°C", "#e06666"),
        ("swvl1", "Soil Moisture ($\\theta_{swvl1}$)", "m³/m³", "#6c8ebf"),
        ("pev", "Potential Evaporation ($E_{pev}$)", "m", "#7fbf7f")
    ]
    
    years = annual.index.year.values
    x = np.arange(len(years))
    
    for i, (col, label, units, color) in enumerate(variables):
        ax = axes[i]
        y = annual[col].values
        
        # Plot data points
        ax.plot(years, y, 'o-', color=color, linewidth=1.5, markersize=5, label="Annual Mean")
        
        # Fit regression line
        slope, intercept, r_val, p_val, _ = stats.linregress(x, y)
        y_fit = slope * x + intercept
        sig = "(Significant, p < 0.05)" if p_val < 0.05 else "(Not Significant)"
        
        ax.plot(years, y_fit, '--', color="black", linewidth=1.2, 
                label=f"Trend: {slope:+.4f} {units}/yr\n$R^2$ = {r_val**2:.3f}, p = {p_val:.4f}")
        
        ax.set_title(f"{label} Trend {sig}", fontweight="bold", fontsize=11)
        ax.set_ylabel(f"{units}", fontsize=10)
        ax.legend(loc="upper left", frameon=True)
        ax.grid(True, linestyle=":", alpha=0.6)
        sns.despine(ax=ax)
        
    axes[-1].set_xlabel("Year", fontsize=11)
    plt.tight_layout()
    fig.savefig("reports/figures/01_climatic_trends.png")
    plt.close(fig)
    print("Figure 1 generated successfully.")

if __name__ == "__main__":
    main()
