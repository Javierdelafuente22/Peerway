"""
Evaluation and reporting module.

Strategy:
    1. Run the trained policy through the dataset day-by-day
    2. Apply battery actions to modify 1_Prosumer's net demand
    3. Save the modified dataset as a CSV
    4. Run orderbook_basic.py on that CSV to get exact KPIs
    
This guarantees identical KPI computation to existing benchmarks.
"""

import numpy as np
import pandas as pd
import os

from rl_env.battery import Battery
from rl_env.p2p_energy_env import ACTION_MAP

TARGET_AGENT = '1_Prosumer'
MARKET_FEATURES = [
    'import_price', 'export_price', 'spread', 'net_community',
    'time_day_sin', 'time_day_cos', 'time_year_sin', 'time_year_cos',
    'is_working_day'
]


def generate_modified_csv(df, policy_fn, output_csv, episode_length=24):
    """
    Run a policy through the dataset and save a modified CSV
    where 1_Prosumer's demand reflects battery actions.
    
    The modified CSV can then be fed directly into orderbook_basic.py
    for exact KPI computation.
    
    Args:
        df:             DataFrame (test set or full dataset).
        policy_fn:      Function: observation (np.array) -> action (int).
        output_csv:     Path to save the modified CSV.
        episode_length: Steps per episode (24 = 1 day).
    
    Returns:
        modified_df:    The modified DataFrame (also saved to output_csv).
        soc_log:        List of SoC values at each timestep.
    """
    total_rows = len(df)
    total_days = total_rows // episode_length
    usable_rows = total_days * episode_length
    
    # Work on a copy
    modified_df = df.iloc[:usable_rows].copy().reset_index(drop=True)
    
    # Add columns for tracking (kept in modified_df but NOT in the saved CSV)
    modified_df[f'{TARGET_AGENT}_Raw'] = modified_df[TARGET_AGENT].copy()
    modified_df[f'{TARGET_AGENT}_SoC'] = 0.0
    modified_df[f'{TARGET_AGENT}_Action'] = 0
    
    battery = Battery(capacity=1.0, max_rate=0.4, efficiency=0.95, initial_soc=0.0)
    soc_log = []
    
    for day in range(total_days):
        battery.reset()
        
        for step in range(episode_length):
            idx = day * episode_length + step
            if idx >= usable_rows:
                break
            
            row = modified_df.iloc[idx]
            raw_demand = float(row[f'{TARGET_AGENT}_Raw'])
            
            # Build observation (same format as RL environment)
            obs = np.zeros(11, dtype=np.float32)
            obs[0] = raw_demand
            obs[1] = battery.soc
            obs[2:11] = np.array([float(row[f]) for f in MARKET_FEATURES], dtype=np.float32)
            
            # Get action from policy
            action = policy_fn(obs)
            action_power = ACTION_MAP[action]
            
            # Apply battery
            demand_delta, new_soc = battery.apply_action(action_power)
            modified_demand = raw_demand + demand_delta
            
            # Write modified demand into the dataframe
            modified_df.at[idx, TARGET_AGENT] = modified_demand
            modified_df.at[idx, f'{TARGET_AGENT}_SoC'] = new_soc
            modified_df.at[idx, f'{TARGET_AGENT}_Action'] = action
            
            soc_log.append(new_soc)
    
    # Save to CSV — drop tracking columns so orderbook_basic.py gets a clean input
    output_df = modified_df.drop(columns=[
        f'{TARGET_AGENT}_Raw', f'{TARGET_AGENT}_SoC', f'{TARGET_AGENT}_Action'
    ])
    output_df.to_csv(output_csv, index=False)
    
    print(f"Modified CSV saved to: {output_csv}")
    print(f"  Days processed: {total_days}")
    print(f"  Rows written:   {usable_rows}")
    
    return modified_df, soc_log


def run_evaluation_pipeline(df, policy_fn, output_dir, policy_name="policy",
                            alpha_file='data/alphas.csv', episode_length=24):
    """
    Full evaluation pipeline:
        1. Generate modified CSV from policy
        2. Run orderbook_basic.py on it for exact KPIs
    
    Args:
        df:             DataFrame (test set).
        policy_fn:      Function: observation (np.array) -> action (int).
        output_dir:     Directory to save results.
        policy_name:    Label for this policy (used in filenames).
        alpha_file:     Path to alphas CSV.
        episode_length: Steps per episode.
    
    Returns:
        modified_df: DataFrame with battery actions applied.
    """
    os.makedirs(output_dir, exist_ok=True)
    
    # Step 1: Generate modified CSV
    modified_csv = os.path.join(output_dir, f'orderbook_modified_{policy_name}.csv')
    modified_df, soc_log = generate_modified_csv(df, policy_fn, modified_csv, episode_length)
    
    # Step 2: Run orderbook_basic.py for exact KPIs
    print(f"\nRunning orderbook clearing for '{policy_name}'...")
    
    from orderbook_basic import run_energy_market_simulation_no_battery
    
    run_energy_market_simulation_no_battery(
        input_file=modified_csv,
        alpha_file=alpha_file,
        detailed_transactions=os.path.join(output_dir, f'detailed_{policy_name}.csv'),
        summary_transactions=os.path.join(output_dir, f'summary_{policy_name}.csv'),
        target_agents=[TARGET_AGENT]
    )
    
    return modified_df


# ---------- Policy wrappers ----------

def no_battery_policy(obs):
    """Baseline: always do nothing (action 0)."""
    return 0


def random_policy(obs):
    """Random: pick a random action each step."""
    return np.random.randint(0, len(ACTION_MAP))
