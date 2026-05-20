#!/usr/bin/env python3
"""
Figure 9: Slopes comparison bar chart + Superposed Epoch Analysis (SEA) composite timeline.
Outputs: reports/figures/09_chsi_event_regime_sea_composite.png

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
    
    # 1. Inside vs Outside Drought (original un-divided drought mask)
    is_drought = np.zeros(len(daily), dtype=bool)
    for dr in droughts:
        start_dt = pd.Timestamp(dr["start"])
        end_dt = pd.Timestamp(dr["end"])
        is_drought = is_drought | ((daily.index >= start_dt) & (daily.index <= end_dt))
        
    is_drought_series = pd.Series(is_drought, index=daily.index)
    daily_drought = daily[is_drought_series]
    daily_non_drought = daily[~is_drought_series]
    
    x_dr = np.arange(len(daily_drought)) / 365.25
    slope_dr, _, _, _, _ = stats.linregress(x_dr, daily_drought["CHSI"].values)
    
    x_ndr = np.arange(len(daily_non_drought)) / 365.25
    slope_ndr, _, _, _, _ = stats.linregress(x_ndr, daily_non_drought["CHSI"].values)
    
    # 2. Before/After Flood analysis
    windows = [1, 2, 5]
    results = []
    
    max_lag_days = 5 * 365
    lags = np.arange(-max_lag_days, max_lag_days + 1)
    composite_matrix = np.full((len(floods), len(lags)), np.nan)
    
    for idx_f, fl in enumerate(floods):
        t0 = pd.Timestamp(fl["start"])
        event_slice = daily.loc[t0 - pd.Timedelta(days=max_lag_days) : t0 + pd.Timedelta(days=max_lag_days)]
        for idx_l, lag in enumerate(lags):
            tgt_dt = t0 + pd.Timedelta(days=lag)
            if tgt_dt in event_slice.index:
                composite_matrix[idx_f, idx_l] = event_slice.loc[tgt_dt, "CHSI"]
                
    composite_mean = np.nanmean(composite_matrix, axis=0)
    composite_sem = np.nanstd(composite_matrix, axis=0) / np.sqrt(len(floods))
    
    for w in windows:
        pre_x, pre_y = [], []
        post_x, post_y = [], []
        
        for fl in floods:
            t0 = pd.Timestamp(fl["start"])
            te = pd.Timestamp(fl["end"])
            
            pre_slice = daily.loc[t0 - pd.Timedelta(days=int(w * 365.25)) : t0]
            if not pre_slice.empty:
                rel_x = (pre_slice.index - t0).total_seconds() / (365.25 * 24 * 3600)
                pre_x.extend(rel_x)
                pre_y.extend(pre_slice["CHSI"].values)
                
            post_slice = daily.loc[te : te + pd.Timedelta(days=int(w * 365.25))]
            if not post_slice.empty:
                rel_x = (post_slice.index - te).total_seconds() / (365.25 * 24 * 3600)
                post_x.extend(rel_x)
                post_y.extend(post_slice["CHSI"].values)
                
        pre_x = np.array(pre_x)
        pre_y = np.array(pre_y)
        slope_pre, _, _, _, _ = stats.linregress(pre_x, pre_y)
        
        post_x = np.array(post_x)
        post_y = np.array(post_y)
        slope_post, _, _, _, _ = stats.linregress(post_x, post_y)
        
        results.append({
            "window": w,
            "pre_slope": slope_pre, "post_slope": slope_post
        })
        
    print("Generating Figure 9: SEA Composite plot...")
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5.5))
    
    labels = ["Inside\nDrought", "Outside\nDrought", "1y Pre", "1y Post", "2y Pre", "2y Post", "5y Pre", "5y Post"]
    slopes = [
        slope_dr, slope_ndr,
        results[0]["pre_slope"], results[0]["post_slope"],
        results[1]["pre_slope"], results[1]["post_slope"],
        results[2]["pre_slope"], results[2]["post_slope"]
    ]
    
    bar_colors = ["#dc2626" if s >= 0 else "#2563eb" for s in slopes]
    
    bars = ax1.bar(labels, slopes, color=bar_colors, edgecolor="black", linewidth=0.6, alpha=0.85)
    ax1.axhline(0, color="black", linestyle="-", linewidth=0.8)
    ax1.set_ylabel("Linear Trend Slope (yr$^{-1}$)", fontsize=12)
    ax1.set_title("A) Regression Slopes by Regime and Lag", fontweight="bold", fontsize=11, loc="left")
    ax1.grid(True, axis="y", linestyle=":", alpha=0.5)
    
    for bar in bars:
        height = bar.get_height()
        va_dir = "bottom" if height >= 0 else "top"
        offset = 0.002 if height >= 0 else -0.002
        ax1.text(bar.get_x() + bar.get_width()/2., height + offset, f"{height:+.4f}",
                 ha="center", va=va_dir, fontsize=9, fontweight="semibold")
                 
    sns.despine(ax=ax1)
    
    x_years = lags / 365.25
    ax2.plot(x_years, composite_mean, color="#1e3a8a", linewidth=2.0, label="Composite Mean CHSI")
    ax2.fill_between(x_years, composite_mean - composite_sem, composite_mean + composite_sem, 
                     color="#1e3a8a", alpha=0.15, label=r"$\pm$ 1 SEM")
    
    ax2.axvline(0, color="#10b981", linestyle="--", linewidth=1.5, label="Hurricane/Flood Onset ($t=0$)")
    ax2.set_xlim(-5.0, 5.0)
    ax2.set_xlabel("Relative Time from Event (Years)", fontsize=12)
    ax2.set_ylabel("CHSI (Composite State)", fontsize=12)
    ax2.set_title("B) CHSI Trajectory Aligned Around Floods", fontweight="bold", fontsize=11, loc="left")
    ax2.grid(True, linestyle=":", alpha=0.5)
    ax2.legend(loc="upper right", frameon=True)
    sns.despine(ax=ax2)
    
    plt.tight_layout()
    fig.savefig("reports/figures/09_chsi_event_regime_sea_composite.png")
    plt.close(fig)
    print("Figure 9 generated successfully.")

if __name__ == "__main__":
    main()
