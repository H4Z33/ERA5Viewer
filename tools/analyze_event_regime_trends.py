#!/usr/bin/env python3
"""
Hydrological Regime and Event-Lag Trend Analysis for CHSI.
Computes linear trends inside/outside droughts and in 1y, 2y, and 5y windows before/after floods.
Generates a 2-panel historical timeline overlaying the regression fit segments (Figure 9).

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
    
    daily["soil_dryness_n"] = 1.0 - daily["swvl1_n"]
    daily["CHSI"] = (daily["t2m_n"] + daily["soil_dryness_n"] + daily["pev_n"]) / 3.0
    return daily

def main():
    print("Loading data...")
    df = load_data()
    daily = calculate_chsi(df)
    
    # Define events
    droughts = [
        {"name": "D1: 1998-03 Drought", "start": "1998-01-01", "end": "2003-12-31", "color": "#ef4444"},
        {"name": "D2: 2011-12 Drought", "start": "2011-01-01", "end": "2012-06-30", "color": "#ef4444"},
        {"name": "D3: 2022 Drought", "start": "2022-03-01", "end": "2022-09-30", "color": "#ef4444"},
        {"name": "D4: 2024 Drought", "start": "2024-03-01", "end": "2024-09-30", "color": "#ef4444"},
    ]
    
    floods = [
        {"name": "F1: Hurricane Keith", "start": "2000-10-01", "end": "2000-10-15", "color": "#10b981"},
        {"name": "F2: 2007 Flooding", "start": "2007-07-01", "end": "2007-07-31", "color": "#10b981"},
        {"name": "F3: Hurricane Alex", "start": "2010-06-15", "end": "2010-07-15", "color": "#10b981"},
        {"name": "F4: Hurricane Ingrid", "start": "2013-09-15", "end": "2013-10-15", "color": "#10b981"},
        {"name": "F5: 2017 Flooding", "start": "2017-09-20", "end": "2017-10-10", "color": "#10b981"},
    ]
    
    # 1. Inside vs Outside Drought
    is_drought = np.zeros(len(daily), dtype=bool)
    for dr in droughts:
        start_dt = pd.Timestamp(dr["start"])
        end_dt = pd.Timestamp(dr["end"])
        is_drought = is_drought | ((daily.index >= start_dt) & (daily.index <= end_dt))
        
    is_drought_series = pd.Series(is_drought, index=daily.index)
    daily_drought = daily[is_drought_series]
    daily_non_drought = daily[~is_drought_series]
    
    # Linear trend inside drought
    x_dr = np.arange(len(daily_drought)) / 365.25
    slope_dr, intercept_dr, r_dr, p_dr, _ = stats.linregress(x_dr, daily_drought["CHSI"].values)
    
    # Linear trend outside drought
    x_ndr = np.arange(len(daily_non_drought)) / 365.25
    slope_ndr, intercept_ndr, r_ndr, p_ndr, _ = stats.linregress(x_ndr, daily_non_drought["CHSI"].values)
    
    print("\n--- REGIME TREND STATS ---")
    print(f"Inside Drought:  Slope = {slope_dr:+.6f}/yr, R^2 = {r_dr**2:.4f}, p = {p_dr:.4e}")
    print(f"Outside Drought: Slope = {slope_ndr:+.6f}/yr, R^2 = {r_ndr**2:.4f}, p = {p_ndr:.4e}")
    
    # 2. Before/After Flood analysis
    windows = [1, 2, 5]  # years
    results = []
    
    for w in windows:
        pre_x, pre_y = [], []
        post_x, post_y = [], []
        
        for fl in floods:
            t0 = pd.Timestamp(fl["start"])
            te = pd.Timestamp(fl["end"])
            
            # Pre-flood window: [t0 - w yr, t0]
            pre_slice = daily.loc[t0 - pd.Timedelta(days=int(w * 365.25)) : t0]
            if not pre_slice.empty:
                rel_x = (pre_slice.index - t0).total_seconds() / (365.25 * 24 * 3600)
                pre_x.extend(rel_x)
                pre_y.extend(pre_slice["CHSI"].values)
                
            # Post-flood window: [te, te + w yr]
            post_slice = daily.loc[te : te + pd.Timedelta(days=int(w * 365.25))]
            if not post_slice.empty:
                rel_x = (post_slice.index - te).total_seconds() / (365.25 * 24 * 3600)
                post_x.extend(rel_x)
                post_y.extend(post_slice["CHSI"].values)
                
        pre_x = np.array(pre_x)
        pre_y = np.array(pre_y)
        slope_pre, int_pre, r_pre, p_pre, _ = stats.linregress(pre_x, pre_y)
        
        post_x = np.array(post_x)
        post_y = np.array(post_y)
        slope_post, int_post, r_post, p_post, _ = stats.linregress(post_x, post_y)
        
        results.append({
            "window": w,
            "pre_slope": slope_pre, "pre_r2": r_pre**2, "pre_p": p_pre,
            "post_slope": slope_post, "post_r2": r_post**2, "post_p": p_post
        })
        
        print(f"\n{w}-Year Window around Floods:")
        print(f"  Pre-Event:  Slope = {slope_pre:+.6f}/yr, R^2 = {r_pre**2:.4f}, p = {p_pre:.4e}")
        print(f"  Post-Event: Slope = {slope_post:+.6f}/yr, R^2 = {r_post**2:.4f}, p = {p_post:.4e}")

    # =========================================================================
    # GENERATING THE CHRONOLOGICAL OVERLAY PLOT (Figure 9)
    # =========================================================================
    print("\nGenerating Figure 9: Chronological overlay plot...")
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(11, 8.5), sharex=True)
    
    # 30-day rolling average for plotting the background state
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
    
    # -------------------------------------------------------------------------
    # PANEL A: DROUGHT REGIME TREND LINES
    # -------------------------------------------------------------------------
    ax1.plot(daily.index, daily["CHSI"], color="#cccccc", alpha=0.25, linewidth=0.5, label="Daily CHSI")
    ax1.plot(daily.index, daily["chsi_30d"], color="#64748b", alpha=0.8, linewidth=1.2, label="CHSI 30-day Avg")
    
    # Shade and overlay trend for each individual drought segment
    for dr in droughts:
        t_start = pd.Timestamp(dr["start"])
        t_end = pd.Timestamp(dr["end"])
        ax1.axvspan(t_start, t_end, color=regime_colors["drought_bg"], alpha=0.6)
        
        # Fit trend line for this specific segment
        seg = daily.loc[t_start:t_end]
        if len(seg) > 5:
            x_ord = seg.index.map(pd.Timestamp.toordinal)
            slope, intercept, _, _, _ = stats.linregress(x_ord, seg["CHSI"].values)
            y_fit = intercept + slope * x_ord
            ax1.plot(seg.index, y_fit, color=regime_colors["drought_line"], linewidth=2.0, linestyle="-")
            
    # Group and overlay trend for non-drought segments
    # Find contiguous blocks of non-drought
    non_drought_runs = []
    current_run = []
    for dt, val in zip(daily.index, is_drought_series):
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
        ax1.plot(seg.index, y_fit, color=regime_colors["non_drought_line"], linewidth=2.0, linestyle="-")
        
    ax1.set_ylabel("CHSI Value")
    ax1.set_ylim(-0.05, 1.05)
    ax1.set_title("A) Hydrological Regimes: Inside vs. Outside Droughts", fontweight="bold", fontsize=11, loc="left")
    ax1.grid(True, linestyle=":", alpha=0.5)
    
    # Legend for Panel A
    legend_a = [
        Patch(facecolor=regime_colors["drought_bg"], alpha=0.6, label="Documented Drought (D1–D4)"),
        plt.Line2D([0], [0], color=regime_colors["drought_line"], linewidth=2.0, label="Drought Regression Slope (+0.0057/yr)"),
        plt.Line2D([0], [0], color=regime_colors["non_drought_line"], linewidth=2.0, label="Non-Drought Regression Slope (+0.0027/yr)"),
    ]
    ax1.legend(handles=legend_a, loc="upper right", frameon=True)
    sns.despine(ax=ax1)
    
    # -------------------------------------------------------------------------
    # PANEL B: PRE/POST FLOOD LEAD/LAG TREND LINES (2-Year Window)
    # -------------------------------------------------------------------------
    ax2.plot(daily.index, daily["CHSI"], color="#cccccc", alpha=0.25, linewidth=0.5, label="Daily CHSI")
    ax2.plot(daily.index, daily["chsi_30d"], color="#64748b", alpha=0.8, linewidth=1.2, label="CHSI 30-day Avg")
    
    # Shade and overlay 2y Pre/Post trend segments around each flood
    for fl in floods:
        t_start = pd.Timestamp(fl["start"])
        t_end = pd.Timestamp(fl["end"])
        ax2.axvspan(t_start, t_end, color=regime_colors["flood_bg"], alpha=0.8)
        
        # 1. 2y Pre-Flood segment: [t0 - 2yr, t0]
        pre_start = t_start - pd.Timedelta(days=int(2 * 365.25))
        pre_seg = daily.loc[pre_start:t_start]
        if len(pre_seg) > 5:
            x_ord = pre_seg.index.map(pd.Timestamp.toordinal)
            slope, intercept, _, _, _ = stats.linregress(x_ord, pre_seg["CHSI"].values)
            y_fit = intercept + slope * x_ord
            ax2.plot(pre_seg.index, y_fit, color=regime_colors["pre_flood"], linewidth=2.0, linestyle="-")
            
        # 2. 2y Post-Flood segment: [te, te + 2yr]
        post_end = t_end + pd.Timedelta(days=int(2 * 365.25))
        post_seg = daily.loc[t_end:post_end]
        if len(post_seg) > 5:
            x_ord = post_seg.index.map(pd.Timestamp.toordinal)
            slope, intercept, _, _, _ = stats.linregress(x_ord, post_seg["CHSI"].values)
            y_fit = intercept + slope * x_ord
            ax2.plot(post_seg.index, y_fit, color=regime_colors["post_flood"], linewidth=2.0, linestyle="-")
            
    ax2.set_ylabel("CHSI Value")
    ax2.set_xlabel("Year")
    ax2.set_ylim(-0.05, 1.05)
    ax2.set_title("B) Lead/Lag Trends: 2 Years Before/After Floods & Hurricanes", fontweight="bold", fontsize=11, loc="left")
    ax2.grid(True, linestyle=":", alpha=0.5)
    
    # Legend for Panel B
    legend_b = [
        Patch(facecolor=regime_colors["flood_bg"], alpha=0.8, label="Documented Flood/Hurricane (F1–F5)"),
        plt.Line2D([0], [0], color=regime_colors["pre_flood"], linewidth=2.0, label="2y Pre-Flood Trend (+0.0236/yr)"),
        plt.Line2D([0], [0], color=regime_colors["post_flood"], linewidth=2.0, label="2y Post-Flood Recovery Trend (+0.0427/yr)"),
    ]
    ax2.legend(handles=legend_b, loc="upper right", frameon=True)
    sns.despine(ax=ax2)
    
    plt.tight_layout()
    fig.savefig("reports/figures/09_chsi_event_regime_trends.png")
    plt.close(fig)
    print("Figure 9 saved successfully.")

if __name__ == "__main__":
    main()
