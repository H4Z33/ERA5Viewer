#!/usr/bin/env python3
"""
Multi-scale Centered Rolling Trend Analysis for CHSI and its Normalized Components.
Calculates centered rolling slopes over seasonal (90-day) and yearly (365-day) windows
for CHSI, temperature, soil dryness, and potential evaporation.
Saves a publication-quality figure:
- reports/figures/06_chsi_rolling_trends_centered.png

Author: Raul Alejandro Morales Rivera
"""
import sqlite3
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.preprocessing import MinMaxScaler
from scipy import stats
from matplotlib.patches import Patch

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
    
    df.dropna(inplace=True)
    return df

def calculate_chsi(df):
    scaler = MinMaxScaler()
    daily = df.resample("1D").mean().dropna()
    
    daily["t2m_n"] = scaler.fit_transform(daily[["t2m"]])[:, 0]
    daily["swvl1_n"] = scaler.fit_transform(daily[["swvl1"]])[:, 0]
    daily["pev_n"] = scaler.fit_transform(daily[["pev"]].abs())[:, 0]
    
    # Soil dryness component is 1 - swvl1_n
    daily["soil_dryness_n"] = 1.0 - daily["swvl1_n"]
    
    # Target definition
    daily["CHSI"] = (daily["t2m_n"] + daily["soil_dryness_n"] + daily["pev_n"]) / 3.0
    return daily

def compute_rolling_slopes_days(series, window_days):
    """Computes centered rolling linear regression slope in units of change per year."""
    slopes = np.full(len(series), np.nan)
    x = np.arange(window_days) / 365.25
    vals = series.values
    half_w = window_days // 2
    
    for i in range(half_w, len(series) - (window_days - half_w)):
        y_slice = vals[i - half_w : i + (window_days - half_w)]
        slope, _, _, _, _ = stats.linregress(x, y_slice)
        slopes[i] = slope
        
    return pd.Series(slopes, index=series.index)

def main():
    print("Loading data...")
    df = load_data()
    daily = calculate_chsi(df)
    
    # 1. Compute global trend
    x_global = np.arange(len(daily)) / 365.25
    slope_g, _, _, _, _ = stats.linregress(x_global, daily["CHSI"].values)
    print(f"Global CHSI slope: {slope_g:+.6f}/year")
    
    # 2. Compute rolling slopes for CHSI and individual components
    print("Calculating centered rolling slopes (seasonal = 90-day, yearly = 365-day)...")
    daily["chsi_slope_sea"] = compute_rolling_slopes_days(daily["CHSI"], 90)
    daily["t2m_slope_sea"] = compute_rolling_slopes_days(daily["t2m_n"], 90)
    daily["soil_slope_sea"] = compute_rolling_slopes_days(daily["soil_dryness_n"], 90)
    daily["pev_slope_sea"] = compute_rolling_slopes_days(daily["pev_n"], 90)
    
    daily["chsi_slope_yr"] = compute_rolling_slopes_days(daily["CHSI"], 365)
    daily["t2m_slope_yr"] = compute_rolling_slopes_days(daily["t2m_n"], 365)
    daily["soil_slope_yr"] = compute_rolling_slopes_days(daily["soil_dryness_n"], 365)
    daily["pev_slope_yr"] = compute_rolling_slopes_days(daily["pev_n"], 365)
    
    # Documented extreme events to overlay on figures
    events = [
        {"name": "D1: 1998-03 Drought", "start": "1998-01-01", "end": "2003-12-31", "color": "#ef4444", "y_sea": 1.55, "y_yr": 0.38},
        {"name": "F1: Hurricane Keith", "start": "2000-10-01", "end": "2000-10-15", "color": "#10b981", "y_sea": -2.0, "y_yr": -0.35},
        {"name": "F2: 2007 Flooding", "start": "2007-07-01", "end": "2007-07-31", "color": "#10b981", "y_sea": -2.0, "y_yr": -0.35},
        {"name": "F3: Hurricane Alex", "start": "2010-06-15", "end": "2010-07-15", "color": "#10b981", "y_sea": -1.4, "y_yr": -0.28},
        {"name": "D2: 2011-12 Drought", "start": "2011-01-01", "end": "2012-06-30", "color": "#ef4444", "y_sea": 1.55, "y_yr": 0.38},
        {"name": "F4: Hurricane Ingrid", "start": "2013-09-15", "end": "2013-10-15", "color": "#10b981", "y_sea": -2.0, "y_yr": -0.35},
        {"name": "F5: 2017 Flooding", "start": "2017-09-20", "end": "2017-10-10", "color": "#10b981", "y_sea": -1.4, "y_yr": -0.28},
        {"name": "D3: 2022 Drought", "start": "2022-03-01", "end": "2022-09-30", "color": "#ef4444", "y_sea": 1.55, "y_yr": 0.38},
        {"name": "D4: 2024 Drought", "start": "2024-03-01", "end": "2024-09-30", "color": "#ef4444", "y_sea": 1.15, "y_yr": 0.30},
    ]
    
    event_patches = [
        Patch(facecolor="#ef4444", alpha=0.15, label="Documented Drought"),
        Patch(facecolor="#10b981", alpha=0.15, label="Documented Flood/Hurricane"),
    ]
    
    # --- Visualization ---
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10.5, 9.5), sharex=True)
    
    # Colors for components
    colors = {
        "chsi": "black",
        "t2m": "#ef4444",         # Red for Temperature
        "soil": "#b45309",        # Earthy Brown for Soil Dryness
        "pev": "#f97316"          # Orange for Potential Evaporation
    }
    
    # Subplot A: Seasonal (90-day) Slopes
    ax1.plot(daily.index, daily["t2m_slope_sea"], color=colors["t2m"], alpha=0.6, linewidth=0.9, label="Temperature Slope ($T_{2m}$)")
    ax1.plot(daily.index, daily["soil_slope_sea"], color=colors["soil"], alpha=0.6, linewidth=0.9, label="Soil Dryness Slope ($1 - swvl1$)")
    ax1.plot(daily.index, daily["pev_slope_sea"], color=colors["pev"], alpha=0.6, linewidth=0.9, label="PEV Slope ($|pev|$)")
    ax1.plot(daily.index, daily["chsi_slope_sea"], color=colors["chsi"], alpha=0.95, linewidth=1.8, label="CHSI Slope (Composite)")
    
    ax1.axhline(0, color="gray", linestyle=":", linewidth=0.8)
    ax1.set_ylabel("Trend Slope (yr$^{-1}$)")
    ax1.set_title("A) Seasonal Rolling Slopes (Centered 90-Day Window, Half Point of Season)", fontweight="bold")
    ax1.grid(True, linestyle=":", alpha=0.5)
    ax1.set_ylim(-2.6, 2.1)
    
    # Subplot B: Yearly (365-day) Slopes
    ax2.plot(daily.index, daily["t2m_slope_yr"], color=colors["t2m"], alpha=0.7, linewidth=1.1, label="Temperature Slope ($T_{2m}$)")
    ax2.plot(daily.index, daily["soil_slope_yr"], color=colors["soil"], alpha=0.7, linewidth=1.1, label="Soil Dryness Slope ($1 - swvl1$)")
    ax2.plot(daily.index, daily["pev_slope_yr"], color=colors["pev"], alpha=0.7, linewidth=1.1, label="PEV Slope ($|pev|$)")
    ax2.plot(daily.index, daily["chsi_slope_yr"], color=colors["chsi"], alpha=0.95, linewidth=2.0, label="CHSI Slope (Composite)")
    
    ax2.axhline(0, color="gray", linestyle=":", linewidth=0.8)
    ax2.set_ylabel("Trend Slope (yr$^{-1}$)")
    ax2.set_xlabel("Year")
    ax2.set_title("B) Yearly Rolling Slopes (Centered 365-Day Window)", fontweight="bold")
    ax2.grid(True, linestyle=":", alpha=0.5)
    ax2.set_ylim(-0.55, 0.48)
    
    # Overlay events
    for ev in events:
        start_t = pd.Timestamp(ev["start"])
        end_t = pd.Timestamp(ev["end"])
        
        # Shading
        ax1.axvspan(start_t, end_t, color=ev["color"], alpha=0.15)
        ax2.axvspan(start_t, end_t, color=ev["color"], alpha=0.15)
        
        # Midpoint for text
        mid_point = start_t + (end_t - start_t) / 2
        
        # Add labels
        ax1.text(mid_point, ev["y_sea"], ev["name"].split(":")[0], color=ev["color"], 
                 fontsize=8, fontweight="bold", ha="center", va="center")
        ax2.text(mid_point, ev["y_yr"], ev["name"].split(":")[0], color=ev["color"], 
                 fontsize=8, fontweight="bold", ha="center", va="center")
                 
    # Build legends
    handles1, labels1 = ax1.get_legend_handles_labels()
    handles1.extend(event_patches)
    ax1.legend(handles=handles1, loc="upper right", ncol=2, frameon=True)
    
    handles2, labels2 = ax2.get_legend_handles_labels()
    handles2.extend(event_patches)
    ax2.legend(handles=handles2, loc="upper right", ncol=2, frameon=True)
    
    sns.despine(ax=ax1)
    sns.despine(ax=ax2)
    
    fig.tight_layout()
    fig.savefig("reports/figures/06_chsi_rolling_trends_centered.png")
    plt.close(fig)
    print("Figure 6 generated successfully at 'reports/figures/06_chsi_rolling_trends_centered.png'.")
    
    # Print statistics for discussion
    print("\n--- Key Statistics for Discussion ---")
    print(f"Max Seasonal CHSI Slope: {daily['chsi_slope_sea'].max():+.5f}/year")
    print(f"Max Yearly CHSI Slope: {daily['chsi_slope_yr'].max():+.5f}/year")
    print(f"Most intense yearly drying periods (top 5 dates):")
    top_yr = daily.sort_values(by="chsi_slope_yr", ascending=False).head(5)
    for idx, row in top_yr.iterrows():
        print(f"  Date: {idx.strftime('%Y-%m-%d')} | CHSI Slope: {row['chsi_slope_yr']:+.5f}/yr | Soil: {row['soil_slope_yr']:+.5f}/yr | T2m: {row['t2m_slope_yr']:+.5f}/yr | PEV: {row['pev_slope_yr']:+.5f}/yr")

if __name__ == "__main__":
    main()
