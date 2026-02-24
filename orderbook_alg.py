import pandas as pd
import numpy as np

def run_energy_market_simulation(input_file, alpha_file, detailed_transactions, summary_transactions):
    # 1. Load Data
    df = pd.read_csv(input_file)
    df_alphas = pd.read_csv(alpha_file)

    metadata_cols = [
        'timestamp', 
        'time_year_sin', 
        'time_year_cos', 
        'time_day_sin', 
        'time_day_cos', 
        'import_price', 
        'export_price'
    ]
    agent_ids = [col for col in df.columns if col not in metadata_cols]
    
    # Containers for results
    p2p_financials = df.copy()
    for agent in agent_ids: 
        p2p_financials[agent] = 0.0
    
    # Metrics tracking for the summary report
    metrics = {agent: {'p2p_kWh': 0.0, 'grid_kWh': 0.0, 'baseline_net': 0.0, 'p2p_net': 0.0} for agent in agent_ids}

    # 2. Simulation Loop
    for index, row in df.iterrows():
        fit = row['export_price']
        tou = row['import_price']
        
        # Calculate Baseline (Grid-Only) for this period
        for agent in agent_ids:
            qty = row[agent]
            if qty > 0: # Agent buys from Grid
                metrics[agent]['baseline_net'] -= qty * tou
            else: # Agent sells to Grid
                metrics[agent]['baseline_net'] += abs(qty) * fit

        # --- P2P Market Logic ---
        if tou <= fit:
            # Rationality Guard: If no benefit exists, everyone uses the Grid
            for agent in agent_ids:
                qty = row[agent]
                val = -qty * tou if qty > 0 else abs(qty) * fit
                p2p_financials.at[index, agent] = val
                metrics[agent]['p2p_net'] += val
                metrics[agent]['grid_kWh'] += abs(qty)
        else:
            # Create orders appending the agent's alpha value for this specific timestamp
            buy_orders = [[a, row[a], df_alphas.at[index, a]] for a in agent_ids if row[a] > 0]
            sell_orders = [[a, abs(row[a]), df_alphas.at[index, a]] for a in agent_ids if row[a] < 0]

            # --- SORTING LOGIC: PRICE-TIME PRIORITY ---
            # Buyers want to buy. Higher alpha = higher bid price. Sort Descending.
            buy_orders.sort(key=lambda x: x[2], reverse=True)
            
            # Sellers want to sell. Lower alpha = lower asking price. Sort Ascending.
            sell_orders.sort(key=lambda x: x[2], reverse=False)

            # Matching Engine (Now processes the most competitive bids first)
            b_idx, s_idx = 0, 0
            while b_idx < len(buy_orders) and s_idx < len(sell_orders):
                # Unpack 3 variables now: agent_id, quantity, alpha
                b_id, b_qty, alpha_b = buy_orders[b_idx]
                s_id, s_qty, alpha_s = sell_orders[s_idx]
                
                trade_qty = min(b_qty, s_qty)
                
                # --- Dynamic Bilateral Pricing ---
                # The trade price is negotiated as the average of their two alpha bidding strategies
                trade_alpha = (alpha_b + alpha_s) / 2.0
                p2p_price = fit + trade_alpha * (tou - fit)
                
                # Financials (P2P Trade)
                p2p_financials.at[index, b_id] -= trade_qty * p2p_price
                p2p_financials.at[index, s_id] += trade_qty * p2p_price
                metrics[b_id]['p2p_net'] -= trade_qty * p2p_price
                metrics[s_id]['p2p_net'] += trade_qty * p2p_price
                
                # Volume Tracking
                metrics[b_id]['p2p_kWh'] += trade_qty
                metrics[s_id]['p2p_kWh'] += trade_qty
                
                buy_orders[b_idx][1] -= trade_qty
                sell_orders[s_idx][1] -= trade_qty
                if buy_orders[b_idx][1] < 1e-9: b_idx += 1
                if sell_orders[s_idx][1] < 1e-9: s_idx += 1
            
            # Grid Settlement for unmatched quantities (Leftovers)
            for i in range(b_idx, len(buy_orders)):
                agent, rem_qty, _ = buy_orders[i]  # Unpack ignoring alpha
                cost = rem_qty * tou
                p2p_financials.at[index, agent] -= cost
                metrics[agent]['p2p_net'] -= cost
                metrics[agent]['grid_kWh'] += rem_qty
                
            for i in range(s_idx, len(sell_orders)):
                agent, rem_qty, _ = sell_orders[i] # Unpack ignoring alpha
                rev = rem_qty * fit
                p2p_financials.at[index, agent] += rev
                metrics[agent]['p2p_net'] += rev
                metrics[agent]['grid_kWh'] += rem_qty

    # 3. Build Savings Report
    report_list = []
    for agent in agent_ids:
        m = metrics[agent]
        total_vol = m['p2p_kWh'] + m['grid_kWh']
        report_list.append({
            'Agent': agent,
            'Baseline Net (£)': round(m['baseline_net'], 4),
            'P2P Net (£)': round(m['p2p_net'], 4),
            'Savings (£)': round(m['p2p_net'] - m['baseline_net'], 4),
            'P2P Traded (kWh)': round(m['p2p_kWh'], 2),
            'Grid Traded (kWh)': round(m['grid_kWh'], 2),
            'Peer Trade %': round((m['p2p_kWh'] / total_vol * 100), 2) if total_vol > 0 else 0
        })

    # 4. Save to files
    pd.DataFrame(report_list).to_csv(summary_transactions, index=False)
    p2p_financials.to_csv(detailed_transactions, index=False)
    print(f"Success. Files generated: {detailed_transactions}, {summary_transactions}")

# Execution
run_energy_market_simulation(
    input_file='data/orderbook.csv', 
    alpha_file='data/alphas.csv', 
    detailed_transactions='orderbook_results/detailed_transactions.csv', 
    summary_transactions='orderbook_results/summary_transactions.csv'
)