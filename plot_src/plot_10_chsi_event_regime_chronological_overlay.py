#!/usr/bin/env python3
"""
Figure 10: Single-panel chronological timeline overlaying regression segments.
Outputs: reports/figures/10_chsi_event_regime_chronological_overlay.png

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

def main():
    print("Loading data...")
    df = load_data()
    daily = calculate_chsi(df)
    
    droughts = [
        {"name": "D1", "start": "1998-01-01", "end": "2003-12-31"},
        {"name": "D2", "start": "2011-01-01", "end": "2012-06-30"},
        {"name": "D3", "start": "2022-03-01", "end": "2022-09-30"},
        {"name": "D4", "start": "2024-03-01", "end": "2024-09-30"},
    ]
    
    floods = [
        {"name": "F1: Hurricane Keith", "start": "2000-10-01", "end": "2000-10-15"},
        {"name": "F2: 2007 Flooding", "start": "2007-07-01", "end": "2007-07-31"},
        {"name": "F3: Hurricane Alex", "start": "2010-06-15", "end": "2010-07-15"},
        {"name": "F4: Hurricane Ingrid", "start": "2013-09-15", "end": "2013-10-15"},
        {"name": "F5: 2017 Flooding", "start": "2017-09-20", "end": "2017-10-10"},
    ]
    
    print("Generating Chronological Overlay plot (Figure 10)...")
    fig, ax = plt.subplots(figsize=(12, 6.5))
    
    daily["chsi_30d"] = daily["CHSI"].rolling(30, center=True).mean()
    
    # Define colors for trend overlay
    regime_colors = {
        "drought_bg": "#fee2e2",  # light red fill
        "drought_line": "#dc2626", # deep red
        "non_drought_line": "#2563eb", # deep blue
        "pre_flood": "#ea580c", # orange
        "post_flood": "#0d9488", # teal
        "flood_bg": "#d1fae5" # light green fill
    }
    
    # Plot background CHSI data
    ax.plot(daily.index, daily["CHSI"], color="#cccccc", alpha=0.25, linewidth=0.5, label="Daily CHSI")
    ax.plot(daily.index, daily["chsi_30d"], color="#64748b", alpha=0.8, linewidth=1.2, label="CHSI 30-day Avg")
    
    # 1. Segment droughts: split droughts if a flood occurs inside the same timelapse
    divided_droughts = []
    for dr in droughts:
        dr_start = pd.Timestamp(dr["start"])
        dr_end = pd.Timestamp(dr["end"])
        
        # Check if any flood falls inside this drought
        inside_floods = []
        for fl in floods:
            fl_start = pd.Timestamp(fl["start"])
            fl_end = pd.Timestamp(fl["end"])
            if fl_start >= dr_start and fl_end <= dr_end:
                inside_floods.append((fl_start, fl_end))
                
        if inside_floods:
            # Sort floods inside drought by start date
            inside_floods.sort(key=lambda x: x[0])
            
            curr_start = dr_start
            for idx, (fl_start, fl_end) in enumerate(inside_floods):
                if fl_start - pd.Timedelta(days=1) >= curr_start:
                    divided_droughts.append({
                        "name": f"{dr['name']} (Part {chr(97+idx)})",
                        "start": curr_start,
                        "end": fl_start - pd.Timedelta(days=1)
                    })
                curr_start = fl_end + pd.Timedelta(days=1)
            if dr_end >= curr_start:
                divided_droughts.append({
                    "name": f"{dr['name']} (Part {chr(97+len(inside_floods))})",
                    "start": curr_start,
                    "end": dr_end
                })
        else:
            divided_droughts.append({
                "name": dr["name"],
                "start": dr_start,
                "end": dr_end
            })
            
    # Shade and fit regression line for each divided drought segment
    for dr in divided_droughts:
        t_start = dr["start"]
        t_end = dr["end"]
        ax.axvspan(t_start, t_end, color=regime_colors["drought_bg"], alpha=0.6)
        
        seg = daily.loc[t_start:t_end]
        if len(seg) > 5:
            x_ord = seg.index.map(pd.Timestamp.toordinal)
            slope, intercept, _, _, _ = stats.linregress(x_ord, seg["CHSI"].values)
            y_fit = intercept + slope * x_ord
            ax.plot(seg.index, y_fit, color=regime_colors["drought_line"], linewidth=2.0, linestyle="-")
            
    # 2. Shade flood events in green and fit 2y Pre/Post trends
    for fl in floods:
        t_start = pd.Timestamp(fl["start"])
        t_end = pd.Timestamp(fl["end"])
        ax.axvspan(t_start, t_end, color=regime_colors["flood_bg"], alpha=0.8)
        
        # Fit trend pre-flood (2 years)
        pre_start = t_start - pd.Timedelta(days=int(2 * 365.25))
        pre_seg = daily.loc[pre_start:t_start]
        if len(pre_seg) > 5:
            x_ord = pre_seg.index.map(pd.Timestamp.toordinal)
            slope, intercept, _, _, _ = stats.linregress(x_ord, pre_seg["CHSI"].values)
            y_fit = intercept + slope * x_ord
            ax.plot(pre_seg.index, y_fit, color=regime_colors["pre_flood"], linewidth=2.0, linestyle="-")
            
        # Fit trend post-flood (2 years)
        post_end = t_end + pd.Timedelta(days=int(2 * 365.25))
        post_seg = daily.loc[t_end:post_end]
        if len(post_seg) > 5:
            x_ord = post_seg.index.map(pd.Timestamp.toordinal)
            slope, intercept, _, _, _ = stats.linregress(x_ord, post_seg["CHSI"].values)
            y_fit = intercept + slope * x_ord
            ax.plot(post_seg.index, y_fit, color=regime_colors["post_flood"], linewidth=2.0, linestyle="-")

    # 3. Fit regression lines for non-drought runs (divided by both droughts and floods)
    is_drought_or_flood = np.zeros(len(daily), dtype=bool)
    for dr in divided_droughts:
        is_drought_or_flood = is_drought_or_flood | ((daily.index >= dr["start"]) & (daily.index <= dr["end"]))
    for fl in floods:
        is_drought_or_flood = is_drought_or_flood | ((daily.index >= pd.Timestamp(fl["start"])) & (daily.index <= pd.Timestamp(fl["end"])))
        
    non_drought_runs = []
    current_run = []
    for dt, val in zip(daily.index, is_drought_or_flood):
        if not val:
            current_run.append(dt)
        else:
            if len(current_run) > 30:
                non_drought_runs.append(current_run)
            current_run = []
    if len(current_run) > 30:
        non_drought_runs.append(current_run)
        
    for run in non_drought_runs:
        seg = daily.loc[run]
        x_ord = seg.index.map(pd.Timestamp.toordinal)
        slope, intercept, _, _, _ = stats.linregress(x_ord, seg["CHSI"].values)
        y_fit = intercept + slope * x_ord
        ax.plot(seg.index, y_fit, color=regime_colors["non_drought_line"], linewidth=2.0, linestyle="-")
        
    ax.set_ylabel("CHSI Value")
    ax.set_xlabel("Year")
    ax.set_ylim(-0.05, 1.05)
    ax.set_title("Chronological Hydrological Regimes: Overlaid Droughts, Floods, and Lead/Lag Trends", fontweight="bold", fontsize=12)
    ax.grid(True, linestyle=":", alpha=0.5)
    
    # 4. Add seasonal vertical rulers as a secondary top x-axis
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
    
    # Legend
    legend_handles = [
        plt.Line2D([0], [0], color="#cccccc", alpha=0.5, linewidth=0.5, label="Daily CHSI"),
        plt.Line2D([0], [0], color="#64748b", alpha=0.8, linewidth=1.2, label="CHSI 30-day Avg"),
        Patch(facecolor=regime_colors["drought_bg"], alpha=0.6, label="Drought Period (D1–D4)"),
        Patch(facecolor=regime_colors["flood_bg"], alpha=0.8, label="Flood/Hurricane (F1–F5)"),
        plt.Line2D([0], [0], color=regime_colors["drought_line"], linewidth=2.0, label="Drought Regression Trend"),
        plt.Line2D([0], [0], color=regime_colors["non_drought_line"], linewidth=2.0, label="Non-Drought Baseline Trend"),
        plt.Line2D([0], [0], color=regime_colors["pre_flood"], linewidth=2.0, label="2y Pre-Flood Build-up Trend"),
        plt.Line2D([0], [0], color=regime_colors["post_flood"], linewidth=2.0, label="2y Post-Flood Recovery Trend")
    ]
    ax.legend(handles=legend_handles, loc="upper right", frameon=True)
    sns.despine(ax=ax)
    
    plt.tight_layout()
    fig.savefig("reports/figures/10_chsi_event_regime_chronological_overlay.png")
    plt.close(fig)
    print("Figure 10 generated successfully.")

if __name__ == "__main__":
    main()
