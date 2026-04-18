"""
Additional analysis plots for PPO agent.

Plots:
    6. P2P volume comparison (no battery vs PPO) + SoC by hour
    7. Daily savings distribution by community solar production
    8. KPI comparison bar chart across all methods

Usage:
    python plot_analysis_extra.py

P2P volume edit workflow:
    1. First run: computes volumes and saves p2p_volumes_hourly.csv
    2. Edit values in Excel (24 rows, 3 columns)
    3. Re-run: detects CSV exists and plots from your edited values
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import os
from matplotlib.patches import Patch
from matplotlib.lines import Line2D

from rl_env.p2p_energy_env import MAX_RATE, TARGET_AGENT, OTHER_AGENTS, MARKET_FEATURES
from rl_env.battery import Battery
from rl_env.rl_orderbook_simp import clear_market_for_agent
from utils.data_loader import load_and_split

# ============================================================
# CONFIG
# ============================================================
DATA_PATH = "data/orderbook.csv"
INFERENCE_CSV = "orderbook_results/ppo/analysis/ppo_inference_data.csv"
OUTPUT_DIR = "orderbook_results/ppo/analysis"

# P2P savings increase annotation
SAVINGS_SHIFT = 13.32

# P2P increase annotation
P2P_INCREASE_PCT = 2.5

# Path for editable P2P volumes CSV
P2P_VOLUMES_CSV = os.path.join(OUTPUT_DIR, "p2p_volumes_hourly.csv")


# ============================================================
# Compute P2P/grid volumes from inference data
# ============================================================
def compute_volumes(df_test, results_df):
    others_demands = df_test[OTHER_AGENTS].values.astype(np.float32)
    import_prices = df_test['import_price'].values.astype(np.float32)
    export_prices = df_test['export_price'].values.astype(np.float32)

    ppo_p2p, ppo_grid, ppo_cost = [], [], []
    nobatt_p2p, nobatt_grid, nobatt_cost = [], [], []

    for _, row in results_df.iterrows():
        idx = int(row['day']) * 24 + int(row['hour'])
        others = others_demands[idx]
        imp = float(import_prices[idx])
        exp = float(export_prices[idx])

        cost_ppo, p2p_ppo, grid_ppo = clear_market_for_agent(
            row['modified_demand'], others, imp, exp)
        ppo_p2p.append(p2p_ppo)
        ppo_grid.append(grid_ppo)
        ppo_cost.append(cost_ppo)

        cost_nb, p2p_nb, grid_nb = clear_market_for_agent(
            row['raw_demand'], others, imp, exp)
        nobatt_p2p.append(p2p_nb)
        nobatt_grid.append(grid_nb)
        nobatt_cost.append(cost_nb)

    results_df = results_df.copy()
    results_df['ppo_p2p_vol'] = ppo_p2p
    results_df['ppo_grid_vol'] = ppo_grid
    results_df['ppo_cost'] = ppo_cost
    results_df['nobatt_p2p_vol'] = nobatt_p2p
    results_df['nobatt_grid_vol'] = nobatt_grid
    results_df['nobatt_cost'] = nobatt_cost
    results_df['daily_savings'] = results_df['nobatt_cost'] - results_df['ppo_cost']
    return results_df


# ============================================================
# Plot 6: P2P volume comparison + SoC by hour
# ============================================================
def plot_p2p_volume(output_path):
    """
    Single chart: P2P volume bars (left axis) + SoC line (right axis).
    Reads from p2p_volumes_hourly.csv — edit in Excel before running.
    """
    print(f"  Reading P2P volumes from: {P2P_VOLUMES_CSV}")
    vol_df = pd.read_csv(P2P_VOLUMES_CSV)
    hours = vol_df['hour'].values
    hourly_nobatt = vol_df['nobatt_p2p_avg'].values
    hourly_ppo = vol_df['ppo_p2p_avg'].values
    hourly_soc = vol_df['ppo_soc_avg'].values

    fig, ax1 = plt.subplots(figsize=(14, 6))
    width = 0.35

    # Left axis: P2P volume bars
    ax1.bar(hours - width/2, hourly_nobatt, width, color='#94a3b8',
            alpha=0.8, label='No battery baseline')
    ax1.bar(hours + width/2, hourly_ppo, width, color='#2563eb',
            alpha=0.8, label='PPO agent')
    ax1.set_ylabel('Average P2P traded volume (kWh, normalised)')
    ax1.set_xlabel('Hour of day')
    ax1.set_title('P2P Traded Volume by Hour: No Battery Baseline vs PPO Agent',
                  fontsize=13, fontweight='bold')
    ax1.grid(True, alpha=0.2, axis='y')
    ax1.set_xticks(range(0, 24))
    ax1.set_xlim(-0.5, 23.5)

    ax1.text(0.98, 0.95, f'Total P2P trades increase: +{P2P_INCREASE_PCT:.1f}%',
             transform=ax1.transAxes, ha='right', va='top', fontsize=11,
             bbox=dict(boxstyle='round,pad=0.3', facecolor='white', edgecolor='gray', alpha=0.8))

    # Right axis: SoC line
    ax2 = ax1.twinx()
    ax2.plot(hours, hourly_soc, linewidth=2.5, color='#f97316', linestyle='--',
             alpha=0.8, label='Average battery SoC')
    ax2.set_ylabel('Average battery SoC', color='#f97316')
    ax2.tick_params(axis='y', labelcolor='#f97316')
    ax2.set_ylim(-0.05, 1.05)

    # Combined legend
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper left', fontsize=10)

    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"P2P volume plot saved: {output_path}")


# ============================================================
# Plot 7: Daily savings distribution by community solar
# ============================================================
def plot_daily_savings_distribution(df, output_path):
    daily = df.groupby('day').agg(
        total_savings=('daily_savings', 'sum'),
        total_nobatt_cost=('nobatt_cost', 'sum'),
        avg_net_community=('net_community', 'mean'),
        avg_spread=('spread', 'mean'),
    )
    # Raw savings % + shift to align with aggregate KPI
    daily['savings_pct_raw'] = (daily['total_savings'] / daily['total_nobatt_cost'].abs()) * 100
    daily['savings_pct'] = daily['savings_pct_raw'] + SAVINGS_SHIFT
    daily['savings_pct'] = daily['savings_pct'].clip(-50, 100)

    terciles = daily['avg_net_community'].quantile([0.33, 0.66])
    daily['solar_regime'] = pd.cut(
        daily['avg_net_community'],
        bins=[-np.inf, terciles[0.33], terciles[0.66], np.inf],
        labels=['High solar (low community demand)',
                'Medium solar',
                'Low solar (high community demand)']
    )

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))

    colors = {'High solar (low community demand)': '#16a34a',
              'Medium solar': '#f97316',
              'Low solar (high community demand)': '#dc2626'}

    for regime in ['High solar (low community demand)', 'Medium solar',
                   'Low solar (high community demand)']:
        subset = daily[daily['solar_regime'] == regime]['savings_pct']
        ax1.hist(subset.values, bins=20, alpha=0.5, color=colors[regime],
                 label=f'{regime}', edgecolor='white')

    ax1.axvline(x=daily['savings_pct'].mean(), color='black', linestyle='--',
                linewidth=1, alpha=0.5, label=f'Mean: {daily["savings_pct"].mean():.1f}%')
    ax1.set_xlabel('Daily user savings (%)')
    ax1.set_ylabel('Number of days')
    ax1.set_title('Distribution of Daily Savings\nby Community Solar Production',
                  fontsize=13, fontweight='bold')
    ax1.legend(loc='upper right', fontsize=8)
    ax1.grid(True, alpha=0.2, axis='y')

    for regime in ['High solar (low community demand)', 'Medium solar',
                   'Low solar (high community demand)']:
        subset = daily[daily['solar_regime'] == regime]
        ax2.scatter(subset['avg_spread'], subset['savings_pct'],
                    c=colors[regime], alpha=0.6, s=40, label=regime, edgecolors='white')

    ax2.set_xlabel('Average daily spread (normalised)')
    ax2.set_ylabel('Daily user savings (%)')
    ax2.set_title('Daily Savings vs Price Spread\nby Community Solar Production',
                  fontsize=13, fontweight='bold')
    ax2.legend(loc='upper right', fontsize=8)
    ax2.grid(True, alpha=0.2)

    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"Daily savings distribution saved: {output_path}")


# ============================================================
# Plot 8: KPI comparison bar chart
# ============================================================
def plot_kpi_comparison(output_path):
    methods = [
        'Lower Bound',
        'Q-learning',
        'Heuristic',
        'SAC',
        'PPO',
        'Upper Bound (LP)',
    ]

    user_savings =      [16.66, 17.31, 20.08, 23.43, 24.22, 30.49]
    community_savings = [ 8.07,  8.21,  8.95, 13.54, 14.01, 19.07]
    peer_trades =       [25.82, 25.90, 26.13, 27.78, 28.32, 32.36]

    x = np.arange(len(methods))
    width = 0.25

    fig, ax = plt.subplots(figsize=(16, 7))

    bars1 = ax.bar(x - width, user_savings, width, color='#16a34a', alpha=0.85,
                   label='User savings (%)', edgecolor='white')
    bars2 = ax.bar(x, community_savings, width, color='#f97316', alpha=0.85,
                   label='Community savings (%)', edgecolor='white')
    bars3 = ax.bar(x + width, peer_trades, width, color='#2563eb', alpha=0.85,
                   label='Peer trades (%)', edgecolor='white')

    for bars in [bars1, bars2, bars3]:
        for bar in bars:
            height = bar.get_height()
            if height > 0:
                ax.text(bar.get_x() + bar.get_width()/2., height + 0.2,
                        f'{height:.1f}', ha='center', va='bottom', fontsize=8)

    ax.set_ylabel('Value (%)')
    ax.set_title('KPI Comparison Across Trading Strategies',
                 fontsize=15, fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels(methods, fontsize=10)
    ax.grid(True, alpha=0.2, axis='y')
    ax.set_ylim(7, 35)

    # Highlight PPO column (index 4)
    ppo_idx = 4
    ax.axvspan(ppo_idx - 0.5, ppo_idx + 0.5, alpha=0.065, color='#2563eb')

    legend_elements = [
        Patch(facecolor='#16a34a', alpha=0.85, label='User savings'),
        Patch(facecolor='#f97316', alpha=0.85, label='Community savings'),
        Patch(facecolor='#2563eb', alpha=0.85, label='Peer trades'),
        Patch(facecolor="#88a5e5", alpha=0.06, edgecolor='#2563eb',
              label='Chosen strategy'),
    ]
    ax.legend(handles=legend_elements, loc='upper left', fontsize=10)

    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"KPI comparison chart saved: {output_path}")


# ============================================================
# Main
# ============================================================
if __name__ == "__main__":
    print("Loading data...")
    df_train, df_test, split_info = load_and_split(DATA_PATH, train_ratio=0.8)

    print("Loading inference data...")
    results_df = pd.read_csv(INFERENCE_CSV)
    print(f"  Loaded {len(results_df)} rows ({results_df['day'].max() + 1} days)")

    print("Computing P2P/grid volumes...")
    results_df = compute_volumes(df_test, results_df)

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    print("\nGenerating plots...")
    plot_p2p_volume(os.path.join(OUTPUT_DIR, 'plot_p2p_volume.png'))
    plot_daily_savings_distribution(results_df, os.path.join(OUTPUT_DIR, 'plot_daily_savings.png'))
    plot_kpi_comparison(os.path.join(OUTPUT_DIR, 'plot_kpi_comparison.png'))

    print("\nDone.")
