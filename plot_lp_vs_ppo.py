"""
LP vs PPO comparison plot.

Runs LP optimisation day-by-day (matching PPO's daily SoC reset),
extracts hourly SoC and charge/discharge actions, then overlays
both strategies on the same chart.

Usage:
    python plot_lp_vs_ppo.py

Requires: ppo_inference_data.csv from plot_analysis.py
Generates: plot_lp_vs_ppo.png
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import os
import pulp

from utils.data_loader import load_and_split

# ============================================================
# CONFIG
# ============================================================
DATA_PATH = "data/orderbook.csv"
INFERENCE_CSV = "orderbook_results/ppo/analysis/ppo_inference_data.csv"
OUTPUT_DIR = "orderbook_results/ppo/analysis"

TARGET_AGENT = '1_Prosumer'
OTHER_AGENTS = ['2_Prosumer', '3_Prosumer', '4_Prosumer', '5_Prosumer',
                '6_Buyer', '7_Buyer', '8_Seller', '9_Seller', '10_Seller']

BATT_CAPACITY = 1.0
BATT_POWER = 0.4
EFFICIENCY = 0.95


# ============================================================
# Run LP day-by-day to get hourly SoC and actions
# ============================================================
def run_lp_daily(df_test):
    """
    Run LP optimisation for each day independently (SoC resets to 0).
    Returns DataFrame with day, hour, soc, action_power.
    """
    tou = df_test['import_price'].values
    fit = df_test['export_price'].values
    midpoint = (tou + fit) / 2.0
    a1_load = df_test[TARGET_AGENT].values

    others_surplus = df_test[OTHER_AGENTS].apply(lambda x: np.maximum(0, -x)).sum(axis=1).values
    others_shortage = df_test[OTHER_AGENTS].apply(lambda x: np.maximum(0, x)).sum(axis=1).values

    total_days = len(df_test) // 24
    records = []

    for day in range(total_days):
        start = day * 24
        end = start + 24

        prob = pulp.LpProblem(f"Day_{day}", pulp.LpMinimize)
        soc = pulp.LpVariable.dicts("SOC", range(24), 0, BATT_CAPACITY)
        p_charge = pulp.LpVariable.dicts("Charge", range(24), 0, BATT_POWER)
        p_discharge = pulp.LpVariable.dicts("Discharge", range(24), 0, BATT_POWER)
        grid_buy = pulp.LpVariable.dicts("GridBuy", range(24), 0)
        grid_sell = pulp.LpVariable.dicts("GridSell", range(24), 0)
        p2p_buy = pulp.LpVariable.dicts("P2PBuy", range(24), 0)
        p2p_sell = pulp.LpVariable.dicts("P2PSell", range(24), 0)

        prob += pulp.lpSum([
            grid_buy[h] * tou[start + h] + p2p_buy[h] * midpoint[start + h]
            - grid_sell[h] * fit[start + h] - p2p_sell[h] * midpoint[start + h]
            for h in range(24)
        ])

        for h in range(24):
            t = start + h
            if h == 0:
                prob += soc[h] == (p_charge[h] * EFFICIENCY) - (p_discharge[h] / EFFICIENCY)
            else:
                prob += soc[h] == soc[h-1] + (p_charge[h] * EFFICIENCY) - (p_discharge[h] / EFFICIENCY)

            prob += (a1_load[t] + p_charge[h] - p_discharge[h] ==
                     grid_buy[h] + p2p_buy[h] - grid_sell[h] - p2p_sell[h])
            prob += p2p_buy[h] <= others_surplus[t]
            prob += p2p_sell[h] <= others_shortage[t]

        prob.solve(pulp.PULP_CBC_CMD(msg=0))

        for h in range(24):
            charge_val = pulp.value(p_charge[h]) or 0
            discharge_val = pulp.value(p_discharge[h]) or 0
            soc_val = pulp.value(soc[h]) or 0
            # Net action: positive = charging, negative = discharging
            action = charge_val - discharge_val

            records.append({
                'day': day,
                'hour': h,
                'soc': soc_val,
                'action_power': action,
            })

    return pd.DataFrame(records)


# ============================================================
# Plot: LP vs PPO comparison
# ============================================================
def plot_lp_vs_ppo(ppo_df, lp_df, output_path):
    """
    Three panels by spread regime (averaged).
    Each panel shows LP SoC vs PPO SoC + import price.
    """
    # Merge spread info from PPO data
    day_spreads = ppo_df.groupby('day')['spread'].mean()
    terciles = day_spreads.quantile([0.33, 0.66])
    high_days = day_spreads[day_spreads >= terciles[0.66]].index
    med_days = day_spreads[(day_spreads >= terciles[0.33]) & (day_spreads < terciles[0.66])].index
    low_days = day_spreads[day_spreads < terciles[0.33]].index

    regimes = [
        ('High spread days', high_days),
        ('Medium spread days', med_days),
        ('Low spread days', low_days),
    ]

    fig, axes = plt.subplots(3, 1, figsize=(14, 12), sharex=True)
    hours = np.arange(24)

    for i, (ax, (label, day_indices)) in enumerate(zip(axes, regimes)):
        ppo_regime = ppo_df[ppo_df['day'].isin(day_indices)]
        lp_regime = lp_df[lp_df['day'].isin(day_indices)]

        if len(ppo_regime) == 0 or len(lp_regime) == 0:
            continue

        ppo_hourly = ppo_regime.groupby('hour').agg(
            soc=('soc', 'mean'),
            action_power=('action_power', 'mean'),
            import_price=('import_price', 'mean'),
            net_community=('net_community', 'mean'),
        )
        lp_hourly = lp_regime.groupby('hour').agg(
            soc=('soc', 'mean'),
            action_power=('action_power', 'mean'),
        )

        # SoC lines
        ax.plot(hours, ppo_hourly['soc'].values, linewidth=2.5, color='#2563eb',
                label='PPO battery SoC')
        ax.plot(hours, lp_hourly['soc'].values, linewidth=2.5, color='#dc2626',
                linestyle='--', label='LP battery SoC (perfect foresight)')

        # Import price
        ax.plot(hours, ppo_hourly['import_price'].values, linewidth=1.5, color='#f97316',
                linestyle=':', alpha=0.7, label='Import price (p/kWh)')

        # Net community load
        ax.plot(hours, ppo_hourly['net_community'].values, linewidth=1.5, color='#7c3aed',
                linestyle='--', alpha=0.7, label='Net community load (kW)')

        ax.set_ylabel('Value (normalised)')
        ax.set_ylim(-0.05, 1.05)
        ax.set_xlim(-0.5, 23.5)
        ax.set_title(label, fontsize=13, fontweight='bold')
        ax.grid(True, alpha=0.2)
        ax.set_xticks(range(0, 24, 2))

        if i == 0:
            ax.legend(loc='upper left', fontsize=9)

    axes[-1].set_xlabel('Hour of day')
    fig.suptitle('Battery Strategy Comparison: PPO Agent vs LP Upper Bound (Perfect Foresight)',
                 fontsize=15, fontweight='bold', y=1.01)
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"LP vs PPO plot saved: {output_path}")


# ============================================================
# Main
# ============================================================
if __name__ == "__main__":
    print("Loading data...")
    df_train, df_test, split_info = load_and_split(DATA_PATH, train_ratio=0.8)
    print(f"  Test set: {split_info['test_days']} days")

    print("\nLoading PPO inference data...")
    ppo_df = pd.read_csv(INFERENCE_CSV)
    print(f"  {len(ppo_df)} rows")

    print("\nRunning LP optimisation (day-by-day)...")
    lp_df = run_lp_daily(df_test)
    print(f"  {len(lp_df)} rows ({lp_df['day'].max() + 1} days)")

    # Save LP results for reuse
    lp_csv = os.path.join(OUTPUT_DIR, 'lp_inference_data.csv')
    lp_df.to_csv(lp_csv, index=False)
    print(f"  LP data saved to: {lp_csv}")

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    plot_lp_vs_ppo(ppo_df, lp_df, os.path.join(OUTPUT_DIR, 'plot_lp_vs_ppo.png'))

    print("\nDone.")
