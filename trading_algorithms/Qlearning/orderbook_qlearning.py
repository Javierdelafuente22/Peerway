import pandas as pd
import numpy as np
from collections import deque
import time

# Import your RL Battery class
from trading_algorithms.Qlearning.battery_alg_qlearning import QLearningBattery

def run_rl_market_simulation(input_file, alpha_file, detailed_output, summary_output, target_users):
    # 1. Setup & Load Data
    df = pd.read_csv(input_file)
    agent_ids = [c for c in df.columns if c not in ['timestamp', 'time_year_sin', 'time_year_cos', 'time_day_sin', 'time_day_cos', 'import_price', 'export_price']]
    
    df_alphas = pd.read_csv(alpha_file)
    df_alphas.columns = agent_ids
    
    p2p_fin = df.copy()
    for a in agent_ids: p2p_fin[a] = 0.0

    # 2. Initialize the RL Agent
    # We create ONE agent object and load the brain we trained
    # If you trained for '10_Prosumer', this brain carries that experience.
    rl_agent = QLearningBattery(epsilon=0.0) # 0.0 = No random moves, pure expertise
    try:
        rl_agent.q_table = np.load('trained_q_table.npy')
        print("Successfully loaded trained RL brain.")
    except FileNotFoundError:
        print("Error: trained_q_table.npy not found! Run the training script first.")
        return

    # Tracking columns for the RL user
    for u in target_users:
        p2p_fin[f'{u}_Raw'] = 0.0
        p2p_fin[f'{u}_SoC'] = 0.0
        p2p_fin[f'{u}_Final'] = 0.0

    prices = deque(maxlen=48)
    metrics = {a: {'p2p': 0.0, 'grid': 0.0, 'base': 0.0, 'p2p_n': 0.0} for a in agent_ids}
    counts = {'Shortage': 0, 'Surplus': 0, 'Balance': 0}

    # 3. The Simulation Loop
    for idx, row in df.iterrows():
        tou, fit = row['import_price'], row['export_price']
        hour = pd.to_datetime(row['timestamp']).hour
        prices.append(tou)
        
        # Baseline (No battery)
        for a in agent_ids:
            metrics[a]['base'] += (-row[a] * tou) if row[a] > 0 else (abs(row[a]) * fit)

        # RL Thresholds (Must match the training logic exactly)
        f_p, m_p, c_p = None, None, None
        if len(prices) >= 24:
            f_p, m_p, c_p = np.percentile(prices, 20), np.percentile(prices, 50), np.percentile(prices, 80)
            p2p_fin.at[idx, 'Price_Floor_20'] = f_p
            p2p_fin.at[idx, 'Price_Ceil_80'] = c_p

# Apply the RL Brain to target users
        for u in target_users:
            if u in agent_ids:
                p2p_fin.at[idx, f'{u}_Raw'] = row[u]
                
                # IMPORTANT: Added 'hour' and set is_training=False
                row[u], p2p_fin.at[idx, f'{u}_SoC'] = rl_agent.optimize_demand(
                    row[u], tou, f_p, c_p, m_p, hour, is_training=False
                )
                
                p2p_fin.at[idx, f'{u}_Final'] = row[u]

        # --- P2P Matching (The rest of the logic remains the same) ---
        net = sum(row[a] for a in agent_ids)
        state = 'Shortage' if net > 1e-9 else ('Surplus' if net < -1e-9 else 'Balance')
        counts[state] += 1
        p2p_fin.at[idx, 'State'] = state

        if tou <= fit:
            for a in agent_ids:
                val = (-row[a] * tou) if row[a] > 0 else (abs(row[a]) * fit)
                p2p_fin.at[idx, a] = val
                metrics[a]['p2p_n'] += val
                metrics[a]['grid'] += abs(row[a])
        else:
            buys = sorted([[a, row[a], df_alphas.at[idx, a]] for a in agent_ids if row[a] > 0], key=lambda x: x[2], reverse=True)
            sells = sorted([[a, abs(row[a]), df_alphas.at[idx, a]] for a in agent_ids if row[a] < 0], key=lambda x: x[2])
            
            b_i, s_i = 0, 0
            while b_i < len(buys) and s_i < len(sells):
                b_id, s_id = buys[b_i][0], sells[s_i][0]
                t_qty = min(buys[b_i][1], sells[s_i][1])
                pr = fit + ((buys[b_i][2] + sells[s_i][2])/2) * (tou - fit)
                p2p_fin.at[idx, b_id] -= t_qty * pr
                p2p_fin.at[idx, s_id] += t_qty * pr
                metrics[b_id]['p2p_n'] -= t_qty * pr
                metrics[s_id]['p2p_n'] += t_qty * pr
                metrics[b_id]['p2p'] += t_qty
                metrics[s_id]['p2p'] += t_qty
                buys[b_i][1] -= t_qty
                sells[s_i][1] -= t_qty
                if buys[b_i][1] < 1e-9: b_i += 1
                if sells[s_i][1] < 1e-9: s_i += 1
            
            for a, qty, _ in buys[b_i:]:
                cost = qty * tou
                p2p_fin.at[idx, a] -= cost
                metrics[a]['p2p_n'] -= cost
                metrics[a]['grid'] += qty
            for a, qty, _ in sells[s_i:]:
                rev = qty * fit
                p2p_fin.at[idx, a] += rev
                metrics[a]['p2p_n'] += rev
                metrics[a]['grid'] += qty

    # 4. Final Aggregation & Reporting
    report = []
    for a in agent_ids:
        m = metrics[a]
        vol = m['p2p'] + m['grid']
        savings = ((m['p2p_n'] - m['base']) / abs(m['base'])) * 100 if abs(m['base']) > 1e-9 else 0
        report.append({
            'Agent': a, 'Baseline Costs': round(m['base'], 2), 'P2P Costs': round(m['p2p_n'], 2),
            'Savings %': round(savings, 2), 'P2P (kWh)': round(m['p2p'], 2), 
            'Grid (kWh)': round(m['grid'], 2), 'Peer Trade %': round((m['p2p'] / vol * 100), 2) if vol > 0 else 0
        })

    final_df = pd.DataFrame(report)
    tots = {'Agent': 'COMMUNITY TOTAL', 'Baseline Costs': final_df['Baseline Costs'].sum(), 'P2P Costs': final_df['P2P Costs'].sum(),
            'P2P (kWh)': final_df['P2P (kWh)'].sum(), 'Grid (kWh)': final_df['Grid (kWh)'].sum()}
    tots['Savings %'] = round(((tots['P2P Costs'] - tots['Baseline Costs']) / abs(tots['Baseline Costs'])) * 100, 2)

    total_volume = tots['P2P (kWh)'] + tots['Grid (kWh)']
    tots['Peer Trade %'] = round((tots['P2P (kWh)'] / total_volume * 100), 2) if total_volume > 0 else 0
    
    final_df = pd.concat([final_df, pd.DataFrame([tots])], ignore_index=True)
    final_df.to_csv(summary_output, index=False)
    p2p_fin.to_csv(detailed_output, index=False)
    
    print(f"--- RL RESULTS ---")
    print(f"Community Total Savings: {tots['Savings %']}%")
    print(f"Files saved: {summary_output}")

if __name__ == "__main__":
    start = time.time()
    run_rl_market_simulation(
        input_file='data/orderbook.csv', 
        alpha_file='data/alphas.csv', 
        detailed_output='orderbook_results/detailed_rl_results.csv', 
        summary_output='orderbook_results/summary_rl_results.csv',
        target_users=['1_Prosumer']
    )
    print(f"Total Simulation Time: {time.time() - start:.2f}s")