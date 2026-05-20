#!/usr/bin/env python3
"""
Figure 4: Model Cross-Validation Metrics comparison (RF vs GBR).
Outputs: reports/figures/04_ml_comparison.png

Author: Raul Alejandro Morales Rivera
"""
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path

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

def main():
    print("Generating Figure 4: Model Performance Comparison...")
    folds = np.arange(1, 6)
    
    rf_rmse = [0.0150, 0.0138, 0.0107, 0.0089, 0.0095]
    gbr_rmse = [0.0105, 0.0085, 0.0066, 0.0051, 0.0053]
    
    rf_r2 = [0.9817, 0.9876, 0.9916, 0.9937, 0.9937]
    gbr_r2 = [0.9911, 0.9952, 0.9968, 0.9979, 0.9981]
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 4.5))
    
    # 1. RMSE subplot
    ax1.plot(folds, rf_rmse, 'o-', color="#3b82f6", linewidth=2, markersize=6, label="Random Forest (RF)")
    ax1.plot(folds, gbr_rmse, 'd-', color="#ef4444", linewidth=2, markersize=6, label="Gradient Boosting (GBR)")
    ax1.set_xticks(folds)
    ax1.set_xlabel("Cross-Validation Fold")
    ax1.set_ylabel("RMSE")
    ax1.set_title("Root Mean Squared Error (Lower is Better)", fontweight="bold", fontsize=11)
    ax1.legend(loc="upper right", frameon=True)
    ax1.grid(True, linestyle=":", alpha=0.6)
    sns.despine(ax=ax1)
    
    # 2. R2 subplot
    ax2.plot(folds, rf_r2, 'o-', color="#3b82f6", linewidth=2, markersize=6, label="Random Forest (RF)")
    ax2.plot(folds, gbr_r2, 'd-', color="#ef4444", linewidth=2, markersize=6, label="Gradient Boosting (GBR)")
    ax2.set_xticks(folds)
    ax2.set_xlabel("Cross-Validation Fold")
    ax2.set_ylabel("$R^2$ Score")
    ax2.set_title("Coefficient of Determination $R^2$ (Higher is Better)", fontweight="bold", fontsize=11)
    ax2.legend(loc="lower right", frameon=True)
    ax2.grid(True, linestyle=":", alpha=0.6)
    sns.despine(ax=ax2)
    
    plt.tight_layout()
    fig.savefig("reports/figures/04_ml_comparison.png")
    plt.close(fig)
    print("Figure 4 generated successfully.")

if __name__ == "__main__":
    main()
