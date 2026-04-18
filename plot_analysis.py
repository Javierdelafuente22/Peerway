"""
Generate analysis plots from a trained PPO model.

Plots:
    1. Battery SoC trajectory + import price for sample days
    2a. Action bar chart by hour
    2b. Action heatmap across all test days
    3. Community strategy averaged by spread regime
    4. SoC trajectory averaged by spread regime
    5. Community strategy for individual sample days

Usage:
    python plot_analysis.py

No retraining needed. Loads the saved model and runs inference on test set.
Edit the CONFIG section below to change paths or plot parameters.
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import os
from matplotlib.patches import Patch
from matplotlib.lines import Line2D

from rl_env.p2p_energy_env import P2PEnergyTradingEnv, MAX_RATE, TARGET_AGENT, MARKET_FEATURES
from rl_env.battery import Battery
from utils.data_loader import load_and_split

# ============================================================
# CONFIG — edit these paths
# ============================================================
DATA_PATH = "data/orderbook.csv"
MODEL_PATH = "orderbook_results/ppo/training/ppo_p2p_trading.zip"
VEC_NORM_PATH = "orderbook_results/ppo/training/vec_normalize.pkl"
OUTPUT_DIR = "orderbook_results/ppo/analysis"

SAMPLE_DAYS = None  # None = auto-pick (1 high-spread, 1 low-spread, 1 medium)

# Manual shading overrides for community strategy (Plot 3).
# Key = regime index (0=high, 1=medium, 2=low).
# Value = dict mapping hour -> 'charge' or 'discharge'.
SHADING_OVERRIDES = {
    0: {11: 'charge'},
    1: {3: 'charge', 4: 'charge'},
}

# ============================================================
# Load model and run inference
# ============================================================
def run_inference(df_test, model, obs_rms, clip_obs, epsilon):
    """Run trained policy through test set, recording SoC and actions per step."""
    battery = Battery(capacity=1.0, max_rate=0.4, efficiency=0.95, initial_soc=0.0)
    market_features_arr = df_test[MARKET_FEATURES].values.astype(np.float32)
    raw_demands = df_test[TARGET_AGENT].values.astype(np.float32)
    import_prices = df_test['import_price'].values.astype(np.float32)
    export_prices = df_test['export_price'].values.astype(np.float32)
    net_community = df_test['net_community'].values.astype(np.float32)

    total_rows = len(df_test)
    total_days = total_rows // 24
    usable_rows = total_days * 24
    records = []

    for day in range(total_days):
        battery.reset()
        for step in range(24):
            idx = day * 24 + step
            if idx >= usable_rows:
                break
            obs = np.zeros(11, dtype=np.float32)
            obs[0] = raw_demands[idx]
            obs[1] = battery.soc
            obs[2:11] = market_features_arr[idx]
            norm_obs = np.clip(
                (obs - obs_rms.mean) / np.sqrt(obs_rms.var + epsilon),
                -clip_obs, clip_obs
            ).astype(np.float32)
            action, _ = model.predict(norm_obs, deterministic=True)
            action_scalar = float(np.asarray(action).flatten()[0])
            action_power = action_scalar * MAX_RATE
            demand_delta, new_soc = battery.apply_action(action_power)
            records.append({
                'day': day, 'hour': step, 'soc': new_soc,
                'action_scalar': action_scalar, 'action_power': action_power,
                'demand_delta': demand_delta,
                'import_price': float(import_prices[idx]),
                'export_price': float(export_prices[idx]),
                'spread': float(import_prices[idx] - export_prices[idx]),
                'net_community': float(net_community[idx]),
                'raw_demand': float(raw_demands[idx]),
                'modified_demand': float(raw_demands[idx] + demand_delta),
            })
    return pd.DataFrame(records)


# ============================================================
# Plot 1: SoC trajectory + import price for sample days
# ============================================================
def plot_soc_trajectory(df, output_path, sample_days=None):
    if sample_days is None:
        day_spreads = df.groupby('day')['spread'].mean()
        high_day = day_spreads.idxmax()
        low_day = day_spreads.idxmin()
        med_day = day_spreads.index[(day_spreads - day_spreads.median()).abs().argsort()[0]]
        sample_days = [high_day, med_day, low_day]
        labels = ['High spread day', 'Medium spread day', 'Low spread day']
    else:
        labels = [f'Day {d}' for d in sample_days]

    fig, axes = plt.subplots(len(sample_days), 1, figsize=(14, 4 * len(sample_days)), sharex=True)
    if len(sample_days) == 1:
        axes = [axes]
    hours = np.arange(24)

    for i, (ax, day_idx, label) in enumerate(zip(axes, sample_days, labels)):
        day_data = df[df['day'] == day_idx]
        if len(day_data) == 0:
            continue
        ax.plot(hours, day_data['soc'].values, linewidth=2.5, color='#2563eb', label='Battery SoC')
        ax.plot(hours, day_data['import_price'].values, linewidth=2, color='#f97316',
                alpha=0.8, label='Import price (p/kWh)')
        ax.set_ylabel('Value (normalised)')
        ax.set_ylim(-0.05, 1.05)
        actions = day_data['action_power'].values
        charge_added = False
        discharge_added = False
        for h in range(24):
            if actions[h] > 0.01:
                ax.axvspan(h - 0.4, h + 0.4, alpha=0.15, color='#16a34a',
                           label='Charge' if not charge_added else None)
                charge_added = True
            elif actions[h] < -0.01:
                ax.axvspan(h - 0.4, h + 0.4, alpha=0.15, color='#dc2626',
                           label='Discharge' if not discharge_added else None)
                discharge_added = True
        ax.set_title(label, fontsize=13, fontweight='bold')
        ax.set_xlim(-0.5, 23.5)
        ax.set_xticks(range(0, 24, 2))
        ax.grid(True, alpha=0.2)
        if i == 0:
            ax.legend(loc='upper left', fontsize=9)

    axes[-1].set_xlabel('Hour of day')
    fig.suptitle('PPO Agent: Battery SoC & Import Price Trajectory for a Sample Day by Spread Regime',
                 fontsize=15, fontweight='bold', y=1.01)
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"SoC trajectory plot saved: {output_path}")


# ============================================================
# Plot 2a: Average battery action by hour (bar chart)
# ============================================================
def plot_action_bars(df, output_path):
    fig, ax = plt.subplots(figsize=(14, 5))
    hourly_mean = df.groupby('hour')['action_power'].mean()
    hourly_std = df.groupby('hour')['action_power'].std()
    colors = ['#16a34a' if v > 0.01 else '#dc2626' if v < -0.01 else '#94a3b8'
              for v in hourly_mean.values]
    ax.bar(range(24), hourly_mean.values, color=colors, alpha=0.8, edgecolor='white')
    ax.errorbar(range(24), hourly_mean.values, yerr=hourly_std.values * 0.5,
                fmt='none', color='gray', alpha=0.4, capsize=2)
    ax.axhline(y=0, color='black', linewidth=0.5, alpha=0.3)
    ax.set_ylabel('Mean battery power (kW, normalised)')
    ax.set_xlabel('Hour of day')
    ax.set_title('PPO Agent: Average Battery Action by Hour', fontsize=13, fontweight='bold')
    ax.set_xticks(range(0, 24))
    ax.set_xlim(-0.5, 23.5)
    ax.grid(True, alpha=0.2, axis='y')
    legend_elements = [
        Patch(facecolor='#16a34a', alpha=0.8, label='Charge'),
        Patch(facecolor='#dc2626', alpha=0.8, label='Discharge'),
        Line2D([0], [0], color='gray', alpha=0.4, linewidth=1, label='± 0.5 std'),
    ]
    ax.legend(handles=legend_elements, loc='upper right', fontsize=9)
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"Action bars plot saved: {output_path}")


# ============================================================
# Plot 2b: Action heatmap across all test days
# ============================================================
def plot_action_heatmap(df, output_path):
    fig, ax = plt.subplots(figsize=(14, 6))
    n_days = df['day'].max() + 1
    action_matrix = np.zeros((n_days, 24))
    for _, row in df.iterrows():
        action_matrix[int(row['day']), int(row['hour'])] = row['action_power']
    im = ax.imshow(action_matrix, aspect='auto', cmap='RdYlGn',
                   vmin=-MAX_RATE, vmax=MAX_RATE, interpolation='nearest')
    ax.set_xlabel('Hour of day')
    ax.set_ylabel('Test day')
    ax.set_title('Battery Action per Hour Across All Test Days', fontsize=13, fontweight='bold')
    ax.set_xticks(range(0, 24))
    legend_elements = [
        Patch(facecolor='#16a34a', alpha=0.8, label='Charge'),
        Patch(facecolor='#dc2626', alpha=0.8, label='Discharge'),
        Patch(facecolor="#ffecbf", alpha=0.8, label='Hold'),
    ]
    ax.legend(handles=legend_elements, loc='upper right', fontsize=9)
    cbar = plt.colorbar(im, ax=ax, shrink=0.8, pad=0.02)
    cbar.set_label('Battery power (kW, normalised)')
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"Action heatmap saved: {output_path}")


# ============================================================
# Plot 3: Strategy by spread regime — with shading overrides
# ============================================================
def plot_community_strategy(df, output_path):
    day_mean_spread = df.groupby('day')['spread'].mean()
    terciles = day_mean_spread.quantile([0.33, 0.66])
    high_days = day_mean_spread[day_mean_spread >= terciles[0.66]].index
    med_days = day_mean_spread[(day_mean_spread >= terciles[0.33]) &
                               (day_mean_spread < terciles[0.66])].index
    low_days = day_mean_spread[day_mean_spread < terciles[0.33]].index
    regimes = [
        ('High spread days', high_days),
        ('Medium spread days', med_days),
        ('Low spread days', low_days),
    ]

    fig, axes = plt.subplots(3, 1, figsize=(14, 12), sharex=True)
    hours = np.arange(24)

    for idx, (ax, (regime_label, day_indices)) in enumerate(zip(axes, regimes)):
        regime_data = df[df['day'].isin(day_indices)]
        if len(regime_data) == 0:
            continue
        hourly = regime_data.groupby('hour').agg(
            action_power=('action_power', 'mean'),
            soc=('soc', 'mean'),
            import_price=('import_price', 'mean'),
            export_price=('export_price', 'mean'),
            net_community=('net_community', 'mean'),
        )
        p2p_price = (hourly['import_price'] + hourly['export_price']) / 2
        overrides = SHADING_OVERRIDES.get(idx, {})

        charge_added = False
        discharge_added = False
        for h in range(24):
            if h in overrides:
                color = '#16a34a' if overrides[h] == 'charge' else '#dc2626'
                lbl_key = 'charge' if overrides[h] == 'charge' else 'discharge'
                if lbl_key == 'charge':
                    ax.axvspan(h - 0.4, h + 0.4, alpha=0.15, color=color,
                               label='Charge' if not charge_added else None)
                    charge_added = True
                else:
                    ax.axvspan(h - 0.4, h + 0.4, alpha=0.15, color=color,
                               label='Discharge' if not discharge_added else None)
                    discharge_added = True
            elif hourly['action_power'].iloc[h] > 0.005:
                ax.axvspan(h - 0.4, h + 0.4, alpha=0.15, color='#16a34a',
                           label='Charge' if not charge_added else None)
                charge_added = True
            elif hourly['action_power'].iloc[h] < -0.005:
                ax.axvspan(h - 0.4, h + 0.4, alpha=0.15, color='#dc2626',
                           label='Discharge' if not discharge_added else None)
                discharge_added = True

        ax.plot(hours, hourly['soc'].values, linewidth=2.5, color='#2563eb', label='Battery SoC')
        ax.plot(hours, hourly['import_price'].values, linewidth=2, color='#f97316',
                linestyle='-', label='Import price (p/kWh)', alpha=0.9)
        ax.plot(hours, p2p_price.values, linewidth=2, color='#16a34a',
                linestyle='-', label='P2P price (p/kWh)', alpha=0.9)
        ax.plot(hours, hourly['net_community'].values, linewidth=2, color='#7c3aed',
                linestyle='--', label='Net community load (kW)', alpha=0.8)
        ax.set_ylabel('Value (normalised)', fontsize=10)
        ax.set_ylim(-0.05, 1.05)
        ax.set_xlim(-0.5, 23.5)
        ax.set_title(f'{regime_label}', fontsize=12, fontweight='bold')
        ax.grid(True, alpha=0.15)
        ax.set_xticks(range(0, 24))
        if idx == 0:
            ax.legend(loc='upper left', fontsize=8)

    axes[-1].set_xlabel('Hour of day', fontsize=11)
    fig.suptitle('PPO Strategy: Average Global Analysis by Spread Regime',
                 fontsize=15, fontweight='bold', y=1.01)
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"Community strategy plot saved: {output_path}")


# ============================================================
# Plot 4: SoC trajectory AVERAGED by spread regime
# ============================================================
def plot_soc_trajectory_avg(df, output_path):
    day_spreads = df.groupby('day')['spread'].mean()
    terciles = day_spreads.quantile([0.33, 0.66])
    high_days = day_spreads[day_spreads >= terciles[0.66]].index
    med_days = day_spreads[(day_spreads >= terciles[0.33]) & (day_spreads < terciles[0.66])].index
    low_days = day_spreads[day_spreads < terciles[0.33]].index
    regimes = [
        ('High spread days (avg)', high_days),
        ('Medium spread days (avg)', med_days),
        ('Low spread days (avg)', low_days),
    ]

    fig, axes = plt.subplots(3, 1, figsize=(14, 12), sharex=True)
    hours = np.arange(24)

    for i, (ax, (label, day_indices)) in enumerate(zip(axes, regimes)):
        regime_data = df[df['day'].isin(day_indices)]
        if len(regime_data) == 0:
            continue
        hourly = regime_data.groupby('hour').agg(
            soc=('soc', 'mean'),
            import_price=('import_price', 'mean'),
            action_power=('action_power', 'mean'),
        )
        ax.plot(hours, hourly['soc'].values, linewidth=2.5, color='#2563eb',
                label='Battery SoC')
        ax.plot(hours, hourly['import_price'].values, linewidth=2, color='#f97316',
                alpha=0.8, label='Import price (p/kWh)')
        ax.set_ylabel('Value (normalised)')
        ax.set_ylim(-0.05, 1.05)
        charge_added = False
        discharge_added = False
        for h in range(24):
            if hourly['action_power'].iloc[h] > 0.005:
                ax.axvspan(h - 0.4, h + 0.4, alpha=0.15, color='#16a34a',
                           label='Charge' if not charge_added else None)
                charge_added = True
            elif hourly['action_power'].iloc[h] < -0.005:
                ax.axvspan(h - 0.4, h + 0.4, alpha=0.15, color='#dc2626',
                           label='Discharge' if not discharge_added else None)
                discharge_added = True
        ax.set_title(f'{label}', fontsize=13, fontweight='bold')
        ax.set_xlim(-0.5, 23.5)
        ax.set_xticks(range(0, 24, 2))
        ax.grid(True, alpha=0.2)
        if i == 0:
            ax.legend(loc='upper left', fontsize=9)

    axes[-1].set_xlabel('Hour of day')
    fig.suptitle('PPO Agent: Average Battery SoC & Price Trajectory for the Full Test Set by Spread Regime',
                 fontsize=15, fontweight='bold', y=1.01)
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"SoC trajectory (avg) plot saved: {output_path}")


# ============================================================
# Plot 5: Community strategy for INDIVIDUAL sample days
# ============================================================
def plot_community_strategy_individual(df, output_path, sample_days=None):
    if sample_days is None:
        day_spreads = df.groupby('day')['spread'].mean()
        high_day = day_spreads.idxmax()
        low_day = day_spreads.idxmin()
        med_day = day_spreads.index[(day_spreads - day_spreads.median()).abs().argsort()[0]]
        sample_days = [high_day, med_day, low_day]
        labels = ['High spread day', 'Medium spread day', 'Low spread day']
    else:
        labels = [f'Day {d}' for d in sample_days]

    fig, axes = plt.subplots(len(sample_days), 1, figsize=(14, 4 * len(sample_days)), sharex=True)
    if len(sample_days) == 1:
        axes = [axes]
    hours = np.arange(24)

    for i, (ax, day_idx, label) in enumerate(zip(axes, sample_days, labels)):
        day_data = df[df['day'] == day_idx]
        if len(day_data) == 0:
            continue
        p2p_price = (day_data['import_price'].values + day_data['export_price'].values) / 2
        actions = day_data['action_power'].values
        charge_added = False
        discharge_added = False
        for h in range(24):
            if actions[h] > 0.01:
                ax.axvspan(h - 0.4, h + 0.4, alpha=0.15, color='#16a34a',
                           label='Charge' if not charge_added else None)
                charge_added = True
            elif actions[h] < -0.01:
                ax.axvspan(h - 0.4, h + 0.4, alpha=0.15, color='#dc2626',
                           label='Discharge' if not discharge_added else None)
                discharge_added = True
        ax.plot(hours, day_data['soc'].values, linewidth=2.5, color='#2563eb',
                label='Battery SoC', alpha=0.9)
        ax.plot(hours, day_data['import_price'].values, linewidth=2, color='#f97316',
                linestyle='-', label='Import price (p/kWh)', alpha=0.9)
        ax.plot(hours, p2p_price, linewidth=2, color='#16a34a',
                linestyle='-', label='P2P price (p/kWh)', alpha=0.9)
        ax.plot(hours, day_data['net_community'].values, linewidth=2, color='#7c3aed',
                linestyle='--', label='Net community load (kWh)', alpha=0.8)
        ax.set_ylabel('Value (normalised)', fontsize=10)
        ax.set_ylim(-0.05, 1.05)
        ax.set_xlim(-0.5, 23.5)
        ax.set_title(label, fontsize=13, fontweight='bold')
        ax.grid(True, alpha=0.15)
        ax.set_xticks(range(0, 24))
        if i == 0:
            ax.legend(loc='upper left', fontsize=8)

    axes[-1].set_xlabel('Hour of day', fontsize=11)
    fig.suptitle('PPO Strategy: Sample Day Analysis by Spread Regime',
                 fontsize=15, fontweight='bold', y=1.01)
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"Community strategy (individual) plot saved: {output_path}")


# ============================================================
# Main
# ============================================================
if __name__ == "__main__":
    from stable_baselines3 import PPO
    from stable_baselines3.common.vec_env import VecNormalize, DummyVecEnv

    print("Loading data...")
    df_train, df_test, split_info = load_and_split(DATA_PATH, train_ratio=0.8)
    print(f"  Test set: {split_info['test_days']} days ({split_info['test_rows']} rows)")

    print("Loading trained model...")
    model = PPO.load(MODEL_PATH)

    print("Loading VecNormalize stats...")
    def make_dummy_env():
        return P2PEnergyTradingEnv(df_test)
    dummy_env = DummyVecEnv([make_dummy_env])
    vec_norm = VecNormalize.load(VEC_NORM_PATH, dummy_env)
    obs_rms = vec_norm.obs_rms
    clip_obs = vec_norm.clip_obs
    epsilon = vec_norm.epsilon

    print("Running inference on test set...")
    results_df = run_inference(df_test, model, obs_rms, clip_obs, epsilon)
    print(f"  Generated {len(results_df)} step records ({results_df['day'].max() + 1} days)")

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    results_df.to_csv(os.path.join(OUTPUT_DIR, 'ppo_inference_data.csv'), index=False)
    print(f"  Inference data saved to: {OUTPUT_DIR}/ppo_inference_data.csv")

    print("\nGenerating plots...")
    plot_soc_trajectory(results_df, os.path.join(OUTPUT_DIR, 'plot_soc_trajectory.png'),
                        sample_days=SAMPLE_DAYS)
    plot_action_bars(results_df, os.path.join(OUTPUT_DIR, 'plot_action_bars.png'))
    plot_action_heatmap(results_df, os.path.join(OUTPUT_DIR, 'plot_action_heatmap.png'))
    plot_community_strategy(results_df, os.path.join(OUTPUT_DIR, 'plot_community_strategy.png'))
    plot_soc_trajectory_avg(results_df, os.path.join(OUTPUT_DIR, 'plot_soc_trajectory_avg.png'))
    plot_community_strategy_individual(results_df, os.path.join(OUTPUT_DIR, 'plot_community_individual.png'),
                                        sample_days=SAMPLE_DAYS)
    print("\nDone.")
