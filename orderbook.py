import pandas as pd
import numpy as np
import time

# Import your trading strategies
from trading_algorithms.heuristic_alg_v1 import Heuristic_v1

def run_energy_market_simulation(input_file, alpha_file, detailed_transactions, summary_transactions, target_agents, battery_class):
    df = pd.read_csv(input_file)
    # 1. Identify Agents (Excluding market signals and time features)
    agent_ids = [c for c in df.columns if c not in [
        'timestamp', 'time_year_sin', 'time_year_cos', 
        'time_day_sin', 'time_day_cos','is_working_day', 'import_price', 
        'export_price', 'spread','net_community'
    ]]
    
    # 2. Load Alphas (User preferences)
    df_alphas = pd.read_csv(alpha_file)
    df_alphas.columns = agent_ids
    
    # 3. Setup Result Tracking
    p2p_fin = df.copy()
    for a in agent_ids: p2p_fin[a] = 0.0
    
    # Initialize battery objects
    batteries = {u: battery_class() for u in target_agents if u in agent_ids}
    
    for u in batteries.keys():
        p2p_fin[f'{u}_Raw'] = 0.0
        p2p_fin[f'{u}_SoC'] = 0.0
        p2p_fin[f'{u}_Final'] = 0.0

    metrics = {a: {'p2p': 0.0, 'grid': 0.0, 'base': 0.0, 'p2p_n': 0.0} for a in agent_ids}
    counts = {'Shortage': 0, 'Surplus': 0, 'Balance': 0}

    # 4. Simulation Loop
    for idx, row in df.iterrows():
        tou, fit = row['import_price'], row['export_price']
        spread = row.get('spread', 0)
        
        # Calculate Baseline (What would have happened without P2P/Batteries)
        for a in agent_ids:
            metrics[a]['base'] += (-row[a] * tou) if row[a] > 0 else (abs(row[a]) * fit)

        # 5. Execute Agent Strategies
        # We now pass only market data. The agent handles its own memory/thresholds.
        for u, batt in batteries.items():
            p2p_fin.at[idx, f'{u}_Raw'] = row[u]
            
            # The signature is now agnostic: (net_demand, buy_price, sell_price, spread)
            row[u], p2p_fin.at[idx, f'{u}_SoC'] = batt.optimize_demand(row[u], tou, fit, spread)
            
            p2p_fin.at[idx, f'{u}_Final'] = row[u]

        # 6. Market Clearing (The Orderbook Engine)
        net = sum(row[a] for a in agent_ids)
        state = 'Shortage' if net > 1e-9 else ('Surplus' if net < -1e-9 else 'Balance')
        counts[state] += 1
        p2p_fin.at[idx, 'State'] = state

        if tou <= fit: # Arbitrage check: If grid sell > grid buy, no P2P needed
            for a in agent_ids:
                val = (-row[a] * tou) if row[a] > 0 else (abs(row[a]) * fit)
                p2p_fin.at[idx, a] = val
                metrics[a]['p2p_n'] += val
                metrics[a]['grid'] += abs(row[a])
        else:
            # Matching logic based on Alpha (Time-Price Priority simulation)
            buys = sorted([[a, row[a], df_alphas.at[idx, a]] for a in agent_ids if row[a] > 0], key=lambda x: x[2], reverse=True)
            sells = sorted([[a, abs(row[a]), df_alphas.at[idx, a]] for a in agent_ids if row[a] < 0], key=lambda x: x[2])
            
            b_i, s_i = 0, 0
            while b_i < len(buys) and s_i < len(sells):
                b_id, s_id = buys[b_i][0], sells[s_i][0]
                t_qty = min(buys[b_i][1], sells[s_i][1])
                # Do not erase: Mid-point clearing price weighted by user alpha
                # Do not erase: pr = fit + ((buys[b_i][2] + sells[s_i][2])/2) * (tou - fit)

                # Temporary shportcut: all alphas at 0.5
                pr = fit + 0.5 * (tou - fit)
                
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
            
            # Remaining imbalance goes to Grid
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

    # 7. Reporting Logic
    report = []
    for a in agent_ids:
        m = metrics[a]
        vol = m['p2p'] + m['grid']
        # This is where your code already calculates individual savings
        savings = ((m['p2p_n'] - m['base']) / abs(m['base'])) * 100 if abs(m['base']) > 1e-9 else 0
        report.append({
            'Agent': a, 'Baseline Costs': round(m['base'], 2), 'P2P Costs': round(m['p2p_n'], 2),
            'Savings %': round(savings, 2), 'P2P (kWh)': round(m['p2p'], 2), 
            'Grid (kWh)': round(m['grid'], 2), 'Peer Trade %': round((m['p2p'] / vol * 100), 2) if vol > 0 else 0
        })

    final_df = pd.DataFrame(report)
    
    target_user = target_agents[0]
    user_row = final_df[final_df['Agent'] == target_user]
    user_savings = user_row['Savings %'].values[0] if not user_row.empty else 0

    tots = {
        'Agent': 'COMMUNITY TOTAL',
        'Baseline Costs': final_df['Baseline Costs'].sum(), 'P2P Costs': final_df['P2P Costs'].sum(),
        'P2P (kWh)': final_df['P2P (kWh)'].sum(), 'Grid (kWh)': final_df['Grid (kWh)'].sum(),
        'Shortage Periods': counts['Shortage'], 'Surplus Periods': counts['Surplus'], 'Balance Periods': counts['Balance']
    }
    tots['Savings %'] = round(((tots['P2P Costs'] - tots['Baseline Costs']) / abs(tots['Baseline Costs'])) * 100, 2)
    t_vol = tots['P2P (kWh)'] + tots['Grid (kWh)']
    tots['Peer Trade %'] = round((tots['P2P (kWh)'] / t_vol * 100), 2) if t_vol > 0 else 0
    
    final_df = pd.concat([final_df, pd.DataFrame([tots])], ignore_index=True)
    final_df.to_csv(summary_transactions, index=False)
    p2p_fin.to_csv(detailed_transactions, index=False)
    
    print(f"User {target_user} Savings: {user_savings}% | Community Savings: {tots['Savings %']}% | Peer Trade: {tots['Peer Trade %']}%")

if __name__ == "__main__":
    start = time.time()
    run_energy_market_simulation(
        input_file='data/orderbook.csv', 
        alpha_file='data/alphas.csv', 
        detailed_transactions='orderbook_results/detailed_transactions.csv', 
        summary_transactions='orderbook_results/summary_transactions.csv',
        target_agents=['1_Prosumer'],
        battery_class=Heuristic_v1
    )
    print(f"Runtime: {time.time() - start:.4f}s")