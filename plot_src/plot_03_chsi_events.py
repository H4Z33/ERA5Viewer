#!/usr/bin/env python3
"""
Figure 3: CHSI Events Timeline.
Outputs: reports/figures/03_chsi_events.png

Author: Raul Alejandro Morales Rivera
"""
import sqlite3
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.preprocessing import MinMaxScaler
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

def main():
    print("Loading data...")
    df = load_data()
    
    print("Generating Figure 3: CHSI Events Timeline...")
    scaler = MinMaxScaler()
    daily = df.resample("1D").mean().dropna()
    
    t2m_n = scaler.fit_transform(daily[["t2m"]])[:, 0]
    swvl1_n = scaler.fit_transform(daily[["swvl1"]])[:, 0]
    pev_n = scaler.fit_transform(daily[["pev"]].abs())[:, 0]
    
    chsi = (t2m_n + (1 - swvl1_n) + pev_n) / 3.0
    daily["CHSI"] = chsi
    rolling_30 = daily["CHSI"].rolling(30).mean()
    
    fig, ax = plt.subplots(figsize=(10, 4.5))
    ax.plot(daily.index, daily["CHSI"], color="#cccccc", alpha=0.3, linewidth=0.5, label="Daily CHSI")
    ax.plot(rolling_30.index, rolling_30.values, color="#3b82f6", linewidth=1.5, label="CHSI (30-day average)")
    
    # Documented extreme events
    events = [
        {"name": "D1: 1998-03 Drought", "start": "1998-01-01", "end": "2003-12-31", "color": "#ef4444", "y": 0.85},
        {"name": "F1: Hurricane Keith", "start": "2000-10-01", "end": "2000-10-15", "color": "#10b981", "y": 0.15},
        {"name": "F2: 2007 Flooding", "start": "2007-07-01", "end": "2007-07-31", "color": "#10b981", "y": 0.15},
        {"name": "F3: Hurricane Alex", "start": "2010-06-15", "end": "2010-07-15", "color": "#10b981", "y": 0.25},
        {"name": "D2: 2011-12 Drought", "start": "2011-01-01", "end": "2012-06-30", "color": "#ef4444", "y": 0.85},
        {"name": "F4: Hurricane Ingrid", "start": "2013-09-15", "end": "2013-10-15", "color": "#10b981", "y": 0.15},
        {"name": "F5: 2017 Flooding", "start": "2017-09-20", "end": "2017-10-10", "color": "#10b981", "y": 0.25},
        {"name": "D3: 2022 Drought", "start": "2022-03-01", "end": "2022-09-30", "color": "#ef4444", "y": 0.85},
        {"name": "D4: 2024 Drought", "start": "2024-03-01", "end": "2024-09-30", "color": "#ef4444", "y": 0.75},
    ]
    
    for ev in events:
        start_t = pd.Timestamp(ev["start"])
        end_t = pd.Timestamp(ev["end"])
        ax.axvspan(start_t, end_t, color=ev["color"], alpha=0.25)
        # Add labels to regions
        mid_point = start_t + (end_t - start_t) / 2
        ax.text(mid_point, ev["y"], ev["name"].split(":")[0], color=ev["color"], 
                fontsize=8, fontweight="bold", ha="center", va="center")
        
    ax.set_ylabel("CHSI Value", fontsize=11)
    ax.set_xlabel("Year", fontsize=11)
    ax.set_ylim(0, 1.05)
    ax.set_title("CHSI Reconstruction vs. Documented Extreme Events (1998–2025)", fontweight="bold")
    
    # Add seasonal vertical rulers as a secondary top x-axis
    ax_sec = ax.twiny()
    ax_sec.set_xlim(ax.get_xlim())
    start_yr = daily.index.min().year
    end_yr = daily.index.max().year
    seasonal_dates = []
    for yr in range(start_yr - 1, end_yr + 2):
        for m in [3, 6, 9, 12]:
            dt = pd.Timestamp(f"{yr}-{m:02d}-01")
            if daily.index.min() <= dt <= daily.index.max():
                seasonal_dates.append(dt)
    ax_sec.set_xticks(seasonal_dates)
    ax_sec.set_xticklabels([])
    ax_sec.tick_params(axis='x', which='both', length=0)
    ax_sec.grid(True, axis='x', linestyle=':', color='#cbd5e1', alpha=0.4, linewidth=0.7)
    sns.despine(ax=ax_sec, top=True, right=True, left=True, bottom=True)
    
    legend_elements = [
        Patch(facecolor="#ef4444", alpha=0.3, label="Documented Drought"),
        Patch(facecolor="#10b981", alpha=0.3, label="Documented Flood/Hurricane"),
        plt.Line2D([0], [0], color="#3b82f6", linewidth=1.5, label="CHSI 30-day Avg")
    ]
    ax.legend(handles=legend_elements, loc="upper right")
    sns.despine(ax=ax)
    
    plt.tight_layout()
    fig.savefig("reports/figures/03_chsi_events.png")
    plt.close(fig)
    print("Figure 3 generated successfully.")

if __name__ == "__main__":
    main()
