#!/usr/bin/env python3
"""
Hydrological Regime and Event-Lag Trend Analysis (Superposed Epoch Analysis) for CHSI.
Computes linear trends inside/outside droughts and in 1y, 2y, and 5y windows before/after floods.
Generates:
- reports/figures/09_chsi_event_regime_trends.png

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
    
    # 1. Inside vs Outside Drought
    is_drought = np.zeros(len(daily), dtype=bool)
    for dr in droughts:
        start_dt = pd.Timestamp(dr["start"])
        end_dt = pd.Timestamp(dr["end"])
        is_drought = is_drought | ((daily.index >= start_dt) & (daily.index <= end_dt))
        
    daily_drought = daily[is_drought]
    daily_non_drought = daily[~is_drought]
    
    # Linear trend inside drought
    x_dr = np.arange(len(daily_drought)) / 365.25
    slope_dr, intercept_dr, r_dr, p_dr, _ = stats.linregress(x_dr, daily_drought["CHSI"].values)
    
    # Linear trend outside drought
    x_ndr = np.arange(len(daily_non_drought)) / 365.25
    slope_ndr, intercept_ndr, r_ndr, p_ndr, _ = stats.linregress(x_ndr, daily_non_drought["CHSI"].values)
    
    print("\n--- REGIME TREND STATS ---")
    print(f"Inside Drought:  Slope = {slope_dr:+.6f}/yr, R^2 = {r_dr**2:.4f}, p = {p_dr:.4e} (N={len(daily_drought)})")
    print(f"Outside Drought: Slope = {slope_ndr:+.6f}/yr, R^2 = {r_ndr**2:.4f}, p = {p_ndr:.4e} (N={len(daily_non_drought)})")
    
    # 2. Before/After Flood analysis
    windows = [1, 2, 5]  # years
    results = []
    
    # Prepare composite alignment
    # Let's align all flood events at t = 0 (event start) and retrieve a +/- 5 year window
    max_lag_days = 5 * 365
    lags = np.arange(-max_lag_days, max_lag_days + 1)
    composite_matrix = np.full((len(floods), len(lags)), np.nan)
    
    for idx_f, fl in enumerate(floods):
        t0 = pd.Timestamp(fl["start"])
        te = pd.Timestamp(fl["end"])
        
        # Pull +/- 5 year slice
        event_slice = daily.loc[t0 - pd.Timedelta(days=max_lag_days) : t0 + pd.Timedelta(days=max_lag_days)]
        
        # Map to lag index
        for idx_l, lag in enumerate(lags):
            tgt_dt = t0 + pd.Timedelta(days=lag)
            if tgt_dt in event_slice.index:
                composite_matrix[idx_f, idx_l] = event_slice.loc[tgt_dt, "CHSI"]
                
    # Calculate composite mean and SEM
    composite_mean = np.nanmean(composite_matrix, axis=0)
    composite_sem = np.nanstd(composite_matrix, axis=0) / np.sqrt(len(floods))
    
    # Calculate Before/After slopes by aligning and aggregating points
    for w in windows:
        pre_x, pre_y = [], []
        post_x, post_y = [], []
        
        for fl in floods:
            t0 = pd.Timestamp(fl["start"])
            te = pd.Timestamp(fl["end"])
            
            # Pre-flood window: [t0 - w yr, t0]
            pre_slice = daily.loc[t0 - pd.Timedelta(days=int(w * 365.25)) : t0]
            if not pre_slice.empty:
                # x relative in years: [-w, 0]
                rel_x = (pre_slice.index - t0).total_seconds() / (365.25 * 24 * 3600)
                pre_x.extend(rel_x)
                pre_y.extend(pre_slice["CHSI"].values)
                
            # Post-flood window: [te, te + w yr]
            post_slice = daily.loc[te : te + pd.Timedelta(days=int(w * 365.25))]
            if not post_slice.empty:
                # x relative in years: [0, w]
                rel_x = (post_slice.index - te).total_seconds() / (365.25 * 24 * 3600)
                post_x.extend(rel_x)
                post_y.extend(post_slice["CHSI"].values)
                
        # Fit Pre
        pre_x = np.array(pre_x)
        pre_y = np.array(pre_y)
        slope_pre, int_pre, r_pre, p_pre, _ = stats.linregress(pre_x, pre_y)
        
        # Fit Post
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

    # Generate Figure 9
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5.5))
    
    # Panel A: Slopes comparison bar plot
    labels = ["Inside\nDrought", "Outside\nDrought", "1y Pre", "1y Post", "2y Pre", "2y Post", "5y Pre", "5y Post"]
    slopes = [
        slope_dr, slope_ndr,
        results[0]["pre_slope"], results[0]["post_slope"],
        results[1]["pre_slope"], results[1]["post_slope"],
        results[2]["pre_slope"], results[2]["post_slope"]
    ]
    
    # Assign colors: Warm colors for drying (positive slopes), cool colors for wetting (negative slopes)
    bar_colors = ["#dc2626" if s >= 0 else "#2563eb" for s in slopes]
    
    bars = ax1.bar(labels, slopes, color=bar_colors, edgecolor="black", linewidth=0.6, alpha=0.85)
    ax1.axhline(0, color="black", linestyle="-", linewidth=0.8)
    ax1.set_ylabel("Linear Trend Slope (yr$^{-1}$)", fontsize=12)
    ax1.set_title("A) Regression Slopes by Regime and Lag", fontweight="bold", fontsize=11, loc="left")
    ax1.grid(True, axis="y", linestyle=":", alpha=0.5)
    
    # Add values on top of bars
    for bar in bars:
        height = bar.get_height()
        va_dir = "bottom" if height >= 0 else "top"
        offset = 0.002 if height >= 0 else -0.002
        ax1.text(bar.get_x() + bar.get_width()/2., height + offset, f"{height:+.4f}",
                 ha="center", va=va_dir, fontsize=9, fontweight="semibold")
                 
    sns.despine(ax=ax1)
    
    # Panel B: Composite Timeline (Superposed Epoch Analysis)
    x_years = lags / 365.25
    ax2.plot(x_years, composite_mean, color="#1e3a8a", linewidth=2.0, label="Composite Mean CHSI")
    ax2.fill_between(x_years, composite_mean - composite_sem, composite_mean + composite_sem, 
                     color="#1e3a8a", alpha=0.15, label="$\pm$ 1 SEM")
    
    ax2.axvline(0, color="#10b981", linestyle="--", linewidth=1.5, label="Hurricane/Flood Onset ($t=0$)")
    ax2.set_xlim(-5.0, 5.0)
    ax2.set_xlabel("Relative Time from Event (Years)", fontsize=12)
    ax2.set_ylabel("CHSI (Composite State)", fontsize=12)
    ax2.set_title("B) CHSI Trajectory Aligned Around Floods", fontweight="bold", fontsize=11, loc="left")
    ax2.grid(True, linestyle=":", alpha=0.5)
    ax2.legend(loc="upper right", frameon=True)
    sns.despine(ax=ax2)
    
    plt.tight_layout()
    fig.savefig("reports/figures/09_chsi_event_regime_trends.png")
    plt.close(fig)
    print("\nFigure 9 generated and saved to reports/figures/09_chsi_event_regime_trends.png")
    
    # Export results as a Markdown Table text block to easily copy/paste into article_draft
    print("\n--- LaTeX/Markdown Table Output ---")
    print("| Analysis Window | Linear Slope (yr^-1) | R^2 Score | p-value | Interpretation |")
    print("|---|---|---|---|---|")
    print(f"| Inside Drought | {slope_dr:+.6f} | {r_dr**2:.4f} | {p_dr:.2e} | Drying Acceleration |")
    print(f"| Outside Drought | {slope_ndr:+.6f} | {r_ndr**2:.4f} | {p_ndr:.2e} | Gradual Drying Baseline |")
    for r in results:
        w = r["window"]
        print(f"| {w}-Year Pre-Flood | {r['pre_slope']:+.6f} | {r['pre_r2']:.4f} | {r['pre_p']:.2e} | Pre-onset stress build-up |")
        print(f"| {w}-Year Post-Flood | {r['post_slope']:+.6f} | {r['post_r2']:.4f} | {r['post_p']:.2e} | Post-onset recovery rate |")

if __name__ == "__main__":
    main()
