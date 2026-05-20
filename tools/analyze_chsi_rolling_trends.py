#!/usr/bin/env python3
"""
Multi-scale Rolling Trend and Slope Analysis for CHSI.
Compares trailing vs centered rolling averages and slopes, and generates
three publication-quality figures:
1. reports/figures/06_chsi_rolling_trends_trailing.png
2. reports/figures/07_chsi_rolling_trends_centered.png
3. reports/figures/08_chsi_trend_alignment_comparison.png

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
    
    t2m_n = scaler.fit_transform(daily[["t2m"]])[:, 0]
    swvl1_n = scaler.fit_transform(daily[["swvl1"]])[:, 0]
    pev_n = scaler.fit_transform(daily[["pev"]].abs())[:, 0]
    
    # Target definition
    daily["CHSI"] = (t2m_n + (1 - swvl1_n) + pev_n) / 3.0
    return daily

def compute_rolling_slopes_trailing(series, window_years):
    """Computes trailing rolling linear regression slope in yr^-1 units."""
    window_size = int(window_years * 365.25)
    slopes = np.full(len(series), np.nan)
    
    # Pre-build time index in years
    x = np.arange(window_size) / 365.25
    
    # Vectorized loop for sliding window
    vals = series.values
    for i in range(window_size, len(series)):
        y_slice = vals[i - window_size:i]
        slope, _, _, _, _ = stats.linregress(x, y_slice)
        slopes[i] = slope
        
    return pd.Series(slopes, index=series.index)

def compute_rolling_slopes_centered(series, window_years):
    """Computes centered rolling linear regression slope in yr^-1 units."""
    window_size = int(window_years * 365.25)
    slopes = np.full(len(series), np.nan)
    
    # Pre-build time index in years
    x = np.arange(window_size) / 365.25
    
    vals = series.values
    half_w = window_size // 2
    
    for i in range(half_w, len(series) - (window_size - half_w)):
        y_slice = vals[i - half_w : i + (window_size - half_w)]
        slope, _, _, _, _ = stats.linregress(x, y_slice)
        slopes[i] = slope
        
    return pd.Series(slopes, index=series.index)

def main():
    print("Loading data...")
    df = load_data()
    daily = calculate_chsi(df)
    
    # 1. Compute global trend
    x_global = np.arange(len(daily)) / 365.25
    slope_g, intercept_g, r_g, p_g, _ = stats.linregress(x_global, daily["CHSI"].values)
    print(f"Global CHSI slope: {slope_g:+.6f}/year (R2 = {r_g**2:.4f}, p = {p_g:.4f})")
    
    # 2. Compute smooth rolling means (both alignments)
    daily["CHSI_1yr_t"] = daily["CHSI"].rolling(365).mean()
    daily["CHSI_5yr_t"] = daily["CHSI"].rolling(365 * 5).mean()
    
    daily["CHSI_1yr_c"] = daily["CHSI"].rolling(365, center=True).mean()
    daily["CHSI_5yr_c"] = daily["CHSI"].rolling(365 * 5, center=True).mean()
    
    # 3. Compute rolling slopes (both alignments)
    print("Calculating rolling slopes...")
    daily["slope_2yr_t"] = compute_rolling_slopes_trailing(daily["CHSI"], 2)
    daily["slope_5yr_t"] = compute_rolling_slopes_trailing(daily["CHSI"], 5)
    daily["slope_10yr_t"] = compute_rolling_slopes_trailing(daily["CHSI"], 10)
    
    daily["slope_2yr_c"] = compute_rolling_slopes_centered(daily["CHSI"], 2)
    daily["slope_5yr_c"] = compute_rolling_slopes_centered(daily["CHSI"], 5)
    daily["slope_10yr_c"] = compute_rolling_slopes_centered(daily["CHSI"], 10)
    
    # Documented extreme events to overlay on figures
    events = [
        {"name": "D1: 1998-03 Drought", "start": "1998-01-01", "end": "2003-12-31", "color": "#ef4444", "y_ax1": 0.85, "y_ax2": 0.08},
        {"name": "F1: Hurricane Keith", "start": "2000-10-01", "end": "2000-10-15", "color": "#10b981", "y_ax1": 0.15, "y_ax2": -0.04},
        {"name": "F2: 2007 Flooding", "start": "2007-07-01", "end": "2007-07-31", "color": "#10b981", "y_ax1": 0.15, "y_ax2": -0.04},
        {"name": "F3: Hurricane Alex", "start": "2010-06-15", "end": "2010-07-15", "color": "#10b981", "y_ax1": 0.25, "y_ax2": -0.02},
        {"name": "D2: 2011-12 Drought", "start": "2011-01-01", "end": "2012-06-30", "color": "#ef4444", "y_ax1": 0.85, "y_ax2": 0.08},
        {"name": "F4: Hurricane Ingrid", "start": "2013-09-15", "end": "2013-10-15", "color": "#10b981", "y_ax1": 0.15, "y_ax2": -0.04},
        {"name": "F5: 2017 Flooding", "start": "2017-09-20", "end": "2017-10-10", "color": "#10b981", "y_ax1": 0.25, "y_ax2": -0.02},
        {"name": "D3: 2022 Drought", "start": "2022-03-01", "end": "2022-09-30", "color": "#ef4444", "y_ax1": 0.85, "y_ax2": 0.08},
        {"name": "D4: 2024 Drought", "start": "2024-03-01", "end": "2024-09-30", "color": "#ef4444", "y_ax1": 0.75, "y_ax2": 0.06},
    ]
    
    event_patches = [
        Patch(facecolor="#ef4444", alpha=0.18, label="Documented Drought"),
        Patch(facecolor="#10b981", alpha=0.18, label="Documented Flood/Hurricane"),
    ]
    
    def add_events(ax1, ax2):
        for ev in events:
            start_t = pd.Timestamp(ev["start"])
            end_t = pd.Timestamp(ev["end"])
            
            # Shade regions
            ax1.axvspan(start_t, end_t, color=ev["color"], alpha=0.18)
            ax2.axvspan(start_t, end_t, color=ev["color"], alpha=0.18)
            
            # Midpoint for label placing
            mid_point = start_t + (end_t - start_t) / 2
            
            # Labels
            ax1.text(mid_point, ev["y_ax1"], ev["name"].split(":")[0], color=ev["color"], 
                     fontsize=8, fontweight="bold", ha="center", va="center")
            ax2.text(mid_point, ev["y_ax2"], ev["name"].split(":")[0], color=ev["color"], 
                     fontsize=8, fontweight="bold", ha="center", va="center")
                     
    # =========================================================================
    # FIGURE 6: TRAILING WINDOWS
    # =========================================================================
    fig6, (f6_ax1, f6_ax2) = plt.subplots(2, 1, figsize=(10, 8.5), sharex=True)
    
    # Subplot A
    f6_ax1.plot(daily.index, daily["CHSI"], color="#cccccc", alpha=0.25, linewidth=0.4, label="Daily CHSI")
    f6_ax1.plot(daily.index, daily["CHSI_1yr_t"], color="#3b82f6", alpha=0.8, linewidth=1.2, label="1-Year Rolling Mean (Seasonal Filter)")
    f6_ax1.plot(daily.index, daily["CHSI_5yr_t"], color="#1e3a8a", alpha=1.0, linewidth=2.0, label="5-Year Rolling Mean (Decadal Mode)")
    y_global_fit = slope_g * x_global + intercept_g
    f6_ax1.plot(daily.index, y_global_fit, "--", color="black", linewidth=1.2, label=f"Long-term Trend ({slope_g:+.5f}/yr)")
    f6_ax1.set_ylabel("CHSI Value")
    f6_ax1.set_title("A) Smooth Long-term Climatological Moving Averages (Trailing 1998–2025)", fontweight="bold")
    f6_ax1.grid(True, linestyle=":", alpha=0.5)
    f6_ax1.set_ylim(0, 1.05)
    sns.despine(ax=f6_ax1)
    
    # Subplot B
    f6_ax2.plot(daily.index, daily["slope_2yr_t"], color="#f87171", alpha=0.7, linewidth=0.8, label="2-Year Rolling Slope")
    f6_ax2.plot(daily.index, daily["slope_5yr_t"], color="#ef4444", alpha=0.9, linewidth=1.3, label="5-Year Rolling Slope")
    f6_ax2.plot(daily.index, daily["slope_10yr_t"], color="#b91c1c", alpha=1.0, linewidth=2.0, label="10-Year Rolling Slope")
    f6_ax2.axhline(slope_g, color="black", linestyle="--", linewidth=1.2, label=f"Global Trend Baseline ({slope_g:+.5f}/yr)")
    f6_ax2.axhline(0, color="gray", linestyle=":", linewidth=0.8)
    f6_ax2.set_ylabel("Trend Slope (yr$^{-1}$)")
    f6_ax2.set_xlabel("Year")
    f6_ax2.set_title("B) Multi-scale Rolling Slopes (Trailing Alignment)", fontweight="bold")
    f6_ax2.grid(True, linestyle=":", alpha=0.5)
    f6_ax2.set_ylim(-0.06, 0.11)
    sns.despine(ax=f6_ax2)
    
    add_events(f6_ax1, f6_ax2)
    
    # Legends
    handles1, labels1 = f6_ax1.get_legend_handles_labels()
    handles1.extend(event_patches)
    f6_ax1.legend(handles=handles1, loc="upper right")
    
    handles2, labels2 = f6_ax2.get_legend_handles_labels()
    handles2.extend(event_patches)
    f6_ax2.legend(handles=handles2, loc="upper right")
    
    fig6.tight_layout()
    fig6.savefig("reports/figures/06_chsi_rolling_trends_trailing.png")
    plt.close(fig6)
    print("Figure 6 (Trailing) generated successfully.")

    # =========================================================================
    # FIGURE 7: CENTERED WINDOWS
    # =========================================================================
    fig7, (f7_ax1, f7_ax2) = plt.subplots(2, 1, figsize=(10, 8.5), sharex=True)
    
    # Subplot A
    f7_ax1.plot(daily.index, daily["CHSI"], color="#cccccc", alpha=0.25, linewidth=0.4, label="Daily CHSI")
    f7_ax1.plot(daily.index, daily["CHSI_1yr_c"], color="#3b82f6", alpha=0.8, linewidth=1.2, label="1-Year Rolling Mean (Seasonal Filter)")
    f7_ax1.plot(daily.index, daily["CHSI_5yr_c"], color="#1e3a8a", alpha=1.0, linewidth=2.0, label="5-Year Rolling Mean (Decadal Mode)")
    f7_ax1.plot(daily.index, y_global_fit, "--", color="black", linewidth=1.2, label=f"Long-term Trend ({slope_g:+.5f}/yr)")
    f7_ax1.set_ylabel("CHSI Value")
    f7_ax1.set_title("A) Smooth Long-term Climatological Moving Averages (Centered 1998–2025)", fontweight="bold")
    f7_ax1.grid(True, linestyle=":", alpha=0.5)
    f7_ax1.set_ylim(0, 1.05)
    sns.despine(ax=f7_ax1)
    
    # Subplot B
    f7_ax2.plot(daily.index, daily["slope_2yr_c"], color="#f87171", alpha=0.7, linewidth=0.8, label="2-Year Rolling Slope")
    f7_ax2.plot(daily.index, daily["slope_5yr_c"], color="#ef4444", alpha=0.9, linewidth=1.3, label="5-Year Rolling Slope")
    f7_ax2.plot(daily.index, daily["slope_10yr_c"], color="#b91c1c", alpha=1.0, linewidth=2.0, label="10-Year Rolling Slope")
    f7_ax2.axhline(slope_g, color="black", linestyle="--", linewidth=1.2, label=f"Global Trend Baseline ({slope_g:+.5f}/yr)")
    f7_ax2.axhline(0, color="gray", linestyle=":", linewidth=0.8)
    f7_ax2.set_ylabel("Trend Slope (yr$^{-1}$)")
    f7_ax2.set_xlabel("Year")
    f7_ax2.set_title("B) Multi-scale Rolling Slopes (Centered Alignment)", fontweight="bold")
    f7_ax2.grid(True, linestyle=":", alpha=0.5)
    f7_ax2.set_ylim(-0.06, 0.11)
    sns.despine(ax=f7_ax2)
    
    add_events(f7_ax1, f7_ax2)
    
    # Legends
    handles1, labels1 = f7_ax1.get_legend_handles_labels()
    handles1.extend(event_patches)
    f7_ax1.legend(handles=handles1, loc="upper right")
    
    handles2, labels2 = f7_ax2.get_legend_handles_labels()
    handles2.extend(event_patches)
    f7_ax2.legend(handles=handles2, loc="upper right")
    
    fig7.tight_layout()
    fig7.savefig("reports/figures/07_chsi_rolling_trends_centered.png")
    plt.close(fig7)
    print("Figure 7 (Centered) generated successfully.")

    # =========================================================================
    # FIGURE 8: ALIGNMENT COMPARISON
    # =========================================================================
    fig8, (f8_ax1, f8_ax2) = plt.subplots(2, 1, figsize=(10, 8.5), sharex=True)
    
    # Subplot A: Compare 5-Year Rolling Means
    f8_ax1.plot(daily.index, daily["CHSI_5yr_t"], color="#1e3a8a", linestyle="--", linewidth=1.5, label="5-Year Mean: Trailing (Averaging on last)")
    f8_ax1.plot(daily.index, daily["CHSI_5yr_c"], color="#1d4ed8", linestyle="-", linewidth=2.2, label="5-Year Mean: Centered (+/- 2.5 years)")
    f8_ax1.set_ylabel("CHSI Value")
    f8_ax1.set_title("A) Temporal Phase Shift in 5-Year Climatological Rolling Means", fontweight="bold")
    f8_ax1.grid(True, linestyle=":", alpha=0.5)
    f8_ax1.set_ylim(0.4, 0.65)
    sns.despine(ax=f8_ax1)
    
    # Subplot B: Compare 5-Year and 10-Year Rolling Slopes
    f8_ax2.plot(daily.index, daily["slope_5yr_t"], color="#b91c1c", linestyle="--", linewidth=1.2, label="5-Year Slope: Trailing")
    f8_ax2.plot(daily.index, daily["slope_5yr_c"], color="#ef4444", linestyle="-", linewidth=1.8, label="5-Year Slope: Centered")
    f8_ax2.plot(daily.index, daily["slope_10yr_t"], color="#7f1d1d", linestyle="--", linewidth=1.2, label="10-Year Slope: Trailing")
    f8_ax2.plot(daily.index, daily["slope_10yr_c"], color="#b91c1c", linestyle="-", linewidth=1.8, label="10-Year Slope: Centered")
    
    f8_ax2.axhline(slope_g, color="black", linestyle=":", linewidth=1.0, label="Global Baseline")
    f8_ax2.axhline(0, color="gray", linestyle="-.", linewidth=0.6)
    f8_ax2.set_ylabel("Trend Slope (yr$^{-1}$)")
    f8_ax2.set_xlabel("Year")
    f8_ax2.set_title("B) Phase Differences in Rolling slopes (5-Year & 10-Year)", fontweight="bold")
    f8_ax2.grid(True, linestyle=":", alpha=0.5)
    f8_ax2.set_ylim(-0.04, 0.08)
    sns.despine(ax=f8_ax2)
    
    # Shade and label events on comparison plot
    for ev in events:
        start_t = pd.Timestamp(ev["start"])
        end_t = pd.Timestamp(ev["end"])
        f8_ax1.axvspan(start_t, end_t, color=ev["color"], alpha=0.12)
        f8_ax2.axvspan(start_t, end_t, color=ev["color"], alpha=0.12)
        
        mid_point = start_t + (end_t - start_t) / 2
        f8_ax1.text(mid_point, ev["y_ax1"] * 0.2 + 0.42, ev["name"].split(":")[0], color=ev["color"],
                    fontsize=8, fontweight="bold", ha="center", va="center")
        f8_ax2.text(mid_point, ev["y_ax2"] * 0.6 - 0.01, ev["name"].split(":")[0], color=ev["color"],
                    fontsize=8, fontweight="bold", ha="center", va="center")
                    
    # Legends
    h1, l1 = f8_ax1.get_legend_handles_labels()
    h1.extend(event_patches)
    f8_ax1.legend(handles=h1, loc="upper right")
    
    h2, l2 = f8_ax2.get_legend_handles_labels()
    h2.extend(event_patches)
    f8_ax2.legend(handles=h2, loc="upper right")
    
    fig8.tight_layout()
    fig8.savefig("reports/figures/08_chsi_trend_alignment_comparison.png")
    plt.close(fig8)
    print("Figure 8 (Comparison) generated successfully.")
    
    # Print comparison stats
    print("\n--- Alignment Comparison Stats ---")
    print(f"Max 5-year Trailing Slope: {daily['slope_5yr_t'].max():+.5f}/yr at {daily['slope_5yr_t'].idxmax().strftime('%Y-%m-%d')}")
    print(f"Max 5-year Centered Slope: {daily['slope_5yr_c'].max():+.5f}/yr at {daily['slope_5yr_c'].idxmax().strftime('%Y-%m-%d')}")
    shift_days = (daily['slope_5yr_t'].idxmax() - daily['slope_5yr_c'].idxmax()).days
    print(f"Temporal Shift: {shift_days} days (~{shift_days/365.25:.2f} years)")

if __name__ == "__main__":
    main()
