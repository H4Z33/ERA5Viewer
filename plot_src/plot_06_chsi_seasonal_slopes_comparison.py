#!/usr/bin/env python3
"""
Figure 6: Centered Seasonal Rolling Slopes of CHSI vs. Components (90-Day Window).
Outputs: reports/figures/06_chsi_seasonal_slopes_comparison.png

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
    return df.dropna()

def calculate_chsi(df):
    scaler = MinMaxScaler()
    daily = df.resample("1D").mean().dropna()
    
    daily["t2m_n"] = scaler.fit_transform(daily[["t2m"]])[:, 0]
    daily["swvl1_n"] = scaler.fit_transform(daily[["swvl1"]])[:, 0]
    daily["pev_n"] = scaler.fit_transform(daily[["pev"]].abs())[:, 0]
    
    daily["soil_dryness_n"] = 1.0 - daily["swvl1_n"]
    daily["CHSI"] = (daily["t2m_n"] + daily["soil_dryness_n"] + daily["pev_n"]) / 3.0
    return daily

def compute_rolling_slopes_days(series, window_days):
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
    
    print("Calculating centered seasonal rolling slopes...")
    daily["chsi_slope_sea"] = compute_rolling_slopes_days(daily["CHSI"], 90)
    daily["t2m_slope_sea"] = compute_rolling_slopes_days(daily["t2m_n"], 90)
    daily["soil_slope_sea"] = compute_rolling_slopes_days(daily["soil_dryness_n"], 90)
    daily["pev_slope_sea"] = compute_rolling_slopes_days(daily["pev_n"], 90)
    
    events = [
        {"name": "D1: 1998-03 Drought", "start": "1998-01-01", "end": "2003-12-31", "color": "#ef4444"},
        {"name": "F1: Hurricane Keith", "start": "2000-10-01", "end": "2000-10-15", "color": "#10b981"},
        {"name": "F2: 2007 Flooding", "start": "2007-07-01", "end": "2007-07-31", "color": "#10b981"},
        {"name": "F3: Hurricane Alex", "start": "2010-06-15", "end": "2010-07-15", "color": "#10b981"},
        {"name": "D2: 2011-12 Drought", "start": "2011-01-01", "end": "2012-06-30", "color": "#ef4444"},
        {"name": "F4: Hurricane Ingrid", "start": "2013-09-15", "end": "2013-10-15", "color": "#10b981"},
        {"name": "F5: 2017 Flooding", "start": "2017-09-20", "end": "2017-10-10", "color": "#10b981"},
        {"name": "D3: 2022 Drought", "start": "2022-03-01", "end": "2022-09-30", "color": "#ef4444"},
        {"name": "D4: 2024 Drought", "start": "2024-03-01", "end": "2024-09-30", "color": "#ef4444"},
    ]
    
    event_patches = [
        Patch(facecolor="#ef4444", alpha=0.15, label="Documented Drought"),
        Patch(facecolor="#10b981", alpha=0.15, label="Documented Flood/Hurricane"),
    ]
    
    panels = [
        {"start": "1998-01-01", "end": "2006-12-31", "title": "1) 1998–2006"},
        {"start": "2007-01-01", "end": "2015-12-31", "title": "2) 2007–2015"},
        {"start": "2016-01-01", "end": "2025-12-31", "title": "3) 2016–2025"},
    ]
    
    colors = {
        "chsi": "#1e3a8a",
        "t2m": "#dc2626",
        "soil": "#16a34a",
        "pev": "#7c3aed"
    }
    
    print("Generating Figure 6 (Seasonal Slopes, 3 panels)...")
    fig6, axes6 = plt.subplots(3, 1, figsize=(11, 9.5), sharex=False)
    
    for idx, panel in enumerate(panels):
        ax = axes6[idx]
        p_start = pd.Timestamp(panel["start"])
        p_end = pd.Timestamp(panel["end"])
        
        mask = (daily.index >= p_start) & (daily.index <= p_end)
        df_panel = daily[mask]
        
        ax.plot(df_panel.index, df_panel["t2m_slope_sea"], color=colors["t2m"], alpha=0.7, linewidth=0.9, label="Temperature Slope ($T_{2m}$)")
        ax.plot(df_panel.index, df_panel["soil_slope_sea"], color=colors["soil"], alpha=0.7, linewidth=0.9, label="Soil Dryness Slope ($1 - swvl1$)")
        ax.plot(df_panel.index, df_panel["pev_slope_sea"], color=colors["pev"], alpha=0.7, linewidth=0.9, label="PEV Slope ($|pev|$)")
        ax.plot(df_panel.index, df_panel["chsi_slope_sea"], color=colors["chsi"], alpha=0.95, linewidth=1.8, label="CHSI Slope (Composite)")
        
        ax.axhline(0, color="gray", linestyle=":", linewidth=0.8)
        ax.set_xlim(p_start, p_end)
        ax.set_ylim(-5.2, 4.5)
        ax.set_ylabel("Slope (yr$^{-1}$)")
        ax.set_title(panel["title"], fontweight="bold", fontsize=11, loc="left")
        ax.grid(True, linestyle=":", alpha=0.5)
        sns.despine(ax=ax)
        
        for ev in events:
            ev_start = pd.Timestamp(ev["start"])
            ev_end = pd.Timestamp(ev["end"])
            
            if ev_start <= p_end and ev_end >= p_start:
                ax.axvspan(ev_start, ev_end, color=ev["color"], alpha=0.15)
                visible_start = max(ev_start, p_start)
                visible_end = min(ev_end, p_end)
                mid_point = visible_start + (visible_end - visible_start) / 2
                
                ax.text(mid_point, 0.92, ev["name"].split(":")[0], color=ev["color"], 
                        fontsize=8, fontweight="bold", ha="center", va="center", 
                        transform=ax.get_xaxis_transform(),
                        bbox=dict(facecolor='white', edgecolor='none', alpha=0.75, pad=1))
        
        if idx == 0:
            handles, labels = ax.get_legend_handles_labels()
            handles.extend(event_patches)
            ax.legend(handles=handles, loc="upper right", ncol=3, frameon=True)
            
    fig6.suptitle("Centered Seasonal Rolling Slopes of CHSI vs. Components (90-Day Window)", fontsize=13, fontweight="bold", y=0.98)
    fig6.tight_layout()
    fig6.savefig("reports/figures/06_chsi_seasonal_slopes_comparison.png")
    plt.close(fig6)
    print("Figure 6 generated successfully.")

if __name__ == "__main__":
    main()
