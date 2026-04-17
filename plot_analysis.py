"""
Generate analysis plots from a trained PPO model.

Plots:
    1. Battery SoC trajectory + import price for sample days
    2. Action heatmap: average charge/discharge by hour of day

Usage:
    python plot_analysis.py

No retraining needed. Loads the saved model and runs inference on test set.
Edit the CONFIG section below to change paths or plot parameters.
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import os

from rl_env.p2p_energy_env import P2PEnergyTradingEnv, MAX_RATE, TARGET_AGENT, MARKET_FEATURES
from rl_env.battery import Battery
from utils.data_loader import load_and_split

# ============================================================
# CONFIG — edit these paths
# ============================================================
DATA_PATH = "data/orderbook.csv"
MODEL_PATH = "orderbook_results/ppo/ppo_p2p_trading.zip"
VEC_NORM_PATH = "orderbook_results/ppo/vec_normalize.pkl"
OUTPUT_DIR = "orderbook_results/ppo"

# Days to plot for SoC trajectory (indices into test set days, 0-based)
# Pick 2-3 interesting days, or set to None to auto-pick
SAMPLE_DAYS = None  # None = auto-pick (1 high-spread, 1 low-spread, 1 medium)

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

            # Build 11-dim observation
            obs = np.zeros(11, dtype=np.float32)
            obs[0] = raw_demands[idx]
            obs[1] = battery.soc
            obs[2:11] = market_features_arr[idx]

            # Normalise using saved VecNormalize stats
            norm_obs = np.clip(
                (obs - obs_rms.mean) / np.sqrt(obs_rms.var + epsilon),
                -clip_obs, clip_obs
            ).astype(np.float32)

            # Predict action
            action, _ = model.predict(norm_obs, deterministic=True)
            action_scalar = float(np.asarray(action).flatten()[0])
            action_power = action_scalar * MAX_RATE

            # Apply battery
            demand_delta, new_soc = battery.apply_action(action_power)

            records.append({
                'day': day,
                'hour': step,
                'soc': new_soc,
                'action_scalar': action_scalar,
                'action_power': action_power,
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
    """
    Plot battery SoC and import price over 24 hours for sample days.
    Two y-axes: left = SoC [0,1], right = import price.
    """
    if sample_days is None:
        # Auto-pick: day with highest mean spread, lowest, and median
        day_spreads = df.groupby('day')['spread'].mean()
        high_day = day_spreads.idxmax()
        low_day = day_spreads.idxmin()
        med_day = day_spreads.iloc[(day_spreads - day_spreads.median()).abs().argsort().iloc[0]]
        # Get the actual day index for median
        med_day = day_spreads.index[(day_spreads - day_spreads.median()).abs().argsort()[0]]
        sample_days = [high_day, med_day, low_day]
        labels = ['High spread day', 'Medium spread day', 'Low spread day']
    else:
        labels = [f'Day {d}' for d in sample_days]

    fig, axes = plt.subplots(len(sample_days), 1, figsize=(14, 4 * len(sample_days)),
                              sharex=True)
    if len(sample_days) == 1:
        axes = [axes]

    hours = np.arange(24)

    for ax, day_idx, label in zip(axes, sample_days, labels):
        day_data = df[df['day'] == day_idx]
        if len(day_data) == 0:
            continue

        # Left axis: SoC
        color_soc = '#2563eb'
        ax.plot(hours, day_data['soc'].values, linewidth=2.5, color=color_soc, label='Battery SoC')
        ax.set_ylabel('Battery SoC', color=color_soc)
        ax.tick_params(axis='y', labelcolor=color_soc)
        ax.set_ylim(-0.05, 1.05)

        # Shade charge/discharge actions
        actions = day_data['action_power'].values
        for h in range(24):
            if actions[h] > 0.01:  # Charging
                ax.axvspan(h - 0.4, h + 0.4, alpha=0.15, color='#16a34a')
            elif actions[h] < -0.01:  # Discharging
                ax.axvspan(h - 0.4, h + 0.4, alpha=0.15, color='#dc2626')

        # Right axis: import price
        ax2 = ax.twinx()
        color_price = '#f97316'
        ax2.plot(hours, day_data['import_price'].values, linewidth=2, color=color_price,
                 linestyle='--', alpha=0.8, label='Import price')
        ax2.set_ylabel('Import price', color=color_price)
        ax2.tick_params(axis='y', labelcolor=color_price)

        ax.set_title(label, fontsize=13, fontweight='bold')
        ax.set_xlim(-0.5, 23.5)
        ax.set_xticks(range(0, 24, 2))
        ax.grid(True, alpha=0.2)

        # Combined legend
        lines1, labels1 = ax.get_legend_handles_labels()
        lines2, labels2 = ax2.get_legend_handles_labels()
        ax.legend(lines1 + lines2, labels1 + labels2 +
                  ['Charging', 'Discharging'],
                  loc='upper left', fontsize=9)

    axes[-1].set_xlabel('Hour of day')
    fig.suptitle('PPO Agent: Battery SoC & Price Trajectory', fontsize=15, fontweight='bold', y=1.01)
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"SoC trajectory plot saved: {output_path}")


# ============================================================
# Plot 2: Action heatmap by hour of day
# ============================================================
def plot_action_heatmap(df, output_path):
    """
    Heatmap showing average action (charge/discharge intensity) by hour of day.
    Also shows action distribution as a bar chart.
    """
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 8), height_ratios=[1, 1.2])

    # Top: bar chart of mean action by hour
    hourly_mean = df.groupby('hour')['action_power'].mean()
    hourly_std = df.groupby('hour')['action_power'].std()

    colors = ['#16a34a' if v > 0.01 else '#dc2626' if v < -0.01 else '#94a3b8'
              for v in hourly_mean.values]

    ax1.bar(range(24), hourly_mean.values, color=colors, alpha=0.8, edgecolor='white')
    ax1.errorbar(range(24), hourly_mean.values, yerr=hourly_std.values * 0.5,
                 fmt='none', color='gray', alpha=0.4, capsize=2)
    ax1.axhline(y=0, color='black', linewidth=0.5, alpha=0.3)
    ax1.set_ylabel('Mean battery power\n(+ charge, − discharge)')
    ax1.set_title('PPO Agent: Average Battery Action by Hour', fontsize=13, fontweight='bold')
    ax1.set_xticks(range(0, 24))
    ax1.set_xlim(-0.5, 23.5)
    ax1.grid(True, alpha=0.2, axis='y')

    # Add annotations for peak charge/discharge hours
    max_charge_hour = hourly_mean.idxmax()
    max_discharge_hour = hourly_mean.idxmin()
    ax1.annotate(f'Peak charge\n(hour {max_charge_hour})',
                 xy=(max_charge_hour, hourly_mean[max_charge_hour]),
                 xytext=(max_charge_hour + 2, hourly_mean[max_charge_hour] + 0.05),
                 fontsize=9, ha='center',
                 arrowprops=dict(arrowstyle='->', color='gray', lw=0.8))
    ax1.annotate(f'Peak discharge\n(hour {max_discharge_hour})',
                 xy=(max_discharge_hour, hourly_mean[max_discharge_hour]),
                 xytext=(max_discharge_hour - 2, hourly_mean[max_discharge_hour] - 0.05),
                 fontsize=9, ha='center',
                 arrowprops=dict(arrowstyle='->', color='gray', lw=0.8))

    # Bottom: heatmap showing action distribution across all test days
    n_days = df['day'].max() + 1
    action_matrix = np.zeros((n_days, 24))
    for _, row in df.iterrows():
        action_matrix[int(row['day']), int(row['hour'])] = row['action_power']

    im = ax2.imshow(action_matrix, aspect='auto', cmap='RdYlGn',
                    vmin=-MAX_RATE, vmax=MAX_RATE, interpolation='nearest')
    ax2.set_xlabel('Hour of day')
    ax2.set_ylabel('Test day')
    ax2.set_title('Battery Action per Hour Across All Test Days', fontsize=13, fontweight='bold')
    ax2.set_xticks(range(0, 24))

    cbar = plt.colorbar(im, ax=ax2, shrink=0.8, pad=0.02)
    cbar.set_label('Battery power (green=charge, red=discharge)')

    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"Action heatmap saved: {output_path}")


# ============================================================
# Main
# ============================================================
if __name__ == "__main__":
    from stable_baselines3 import PPO
    from stable_baselines3.common.vec_env import VecNormalize, DummyVecEnv
    import pickle

    print("Loading data...")
    df_train, df_test, split_info = load_and_split(DATA_PATH, train_ratio=0.8)
    print(f"  Test set: {split_info['test_days']} days ({split_info['test_rows']} rows)")

    print("Loading trained model...")
    model = PPO.load(MODEL_PATH)

    print("Loading VecNormalize stats...")
    # Load obs_rms from saved VecNormalize
    # We need to create a dummy VecNormalize to load stats into
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

    # Save raw inference data (useful for further analysis)
    results_df.to_csv(os.path.join(OUTPUT_DIR, 'ppo_inference_data.csv'), index=False)
    print(f"  Inference data saved to: {OUTPUT_DIR}/ppo_inference_data.csv")

    # Generate plots
    print("\nGenerating plots...")
    plot_soc_trajectory(results_df, os.path.join(OUTPUT_DIR, 'plot_soc_trajectory.png'),
                        sample_days=SAMPLE_DAYS)
    plot_action_heatmap(results_df, os.path.join(OUTPUT_DIR, 'plot_action_heatmap.png'))

    print("\nDone.")
