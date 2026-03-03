import pandas as pd
import numpy as np
from collections import deque
import time

# --- 1. SMART BATTERY CLASS ---
class ProsumerBattery:
    def __init__(self, max_rate=0.4, efficiency=0.95, min_soc=0.0, max_soc=1.0):
        self.max_rate = max_rate
        self.efficiency = efficiency
        self.min_soc = min_soc
        self.max_soc = max_soc
        self.soc = min_soc 

    def optimize_demand(self, raw_demand, current_price, floor_p, ceil_p, median_p):
        """
        Logic: 
        1. Always capture personal surplus.
        2. Only self-consume if current price > median (avoid wasting cycles when grid is cheap).
        3. Arbitrage: Charge if price < 20th percentile, Discharge if price > 80th percentile.
        """
        rem_rate = self.max_rate
        
        # Priority 1: Self-Consumption / Surplus Capture
        if raw_demand < 0:  # Surplus
            charge = min(abs(raw_demand), rem_rate, (self.max_soc - self.soc) / self.efficiency)
            self.soc += charge * self.efficiency
            rem_rate -= charge
            raw_demand += charge
            
        elif raw_demand > 0:  # Demand
            # Only discharge if price is high enough (Rationality Guard)
            if median_p is not None and (current_price >= median_p or current_price >= ceil_p):
                available = self.soc - self.min_soc
                discharge = min(raw_demand, rem_rate, available)
                self.soc -= discharge
                rem_rate -= discharge
                raw_demand -= discharge
            
        # Priority 2: Market Arbitrage
        if floor_p is not None and rem_rate > 0:
            # Force Charge (Buy Low)
            if current_price <= floor_p and self.soc < self.max_soc:
                charge = min(rem_rate, (self.max_soc - self.soc) / self.efficiency)
                self.soc += charge * self.efficiency
                raw_demand += charge
            # Force Discharge (Sell High)
            elif current_price >= ceil_p and self.soc > self.min_soc:
                available = self.soc - self.min_soc
                discharge = min(rem_rate, available)
                self.soc -= discharge
                raw_demand -= discharge
                
        return raw_demand, self.soc

# --- 2. SIMULATION ENGINE ---
def run_energy_market_simulation(input_file, alpha_file, detailed_transactions, summary_transactions):
    df = pd.read_csv(input_file)
    agent_ids = [c for c in df.columns if c not in ['timestamp', 'time_year_sin', 'time_year_cos', 'time_day_sin', 'time_day_cos', 'import_price', 'export_price']]
    
    # Header alignment for alphas
    df_alphas = pd.read_csv(alpha_file)
    df_alphas.columns = agent_ids
    df_alphas.to_csv(alpha_file, index=False)
    
    # Containers
    p2p_fin = df.copy()
    for a in agent_ids: p2p_fin[a] = 0.0
    
    # Battery & Memory Initialization
    target = '10_Prosumer'
    batt = ProsumerBattery()
    prices = deque(maxlen=48) # 24-hour rolling window
    
    metrics = {a: {'p2p': 0.0, 'grid': 0.0, 'base': 0.0, 'p2p_n': 0.0} for a in agent_ids}
    counts = {'Shortage': 0, 'Surplus': 0, 'Balance': 0}

    # Simulation Loop
    for idx, row in df.iterrows():
        tou, fit = row['import_price'], row['export_price']
        prices.append(tou)
        
        # 1. Calculate Baseline (No Battery)
        for a in agent_ids:
            metrics[a]['base'] += (-row[a] * tou) if row[a] > 0 else (abs(row[a]) * fit)

        # 2. Smart Battery Logic (Target User Only)
        if target in agent_ids:
            p2p_fin.at[idx, f'{target}_Raw'] = row[target]
            
            # Dynamic Threshold Calculation
            f_p, m_p, c_p = None, None, None
            if len(prices) >= 24:
                f_p, m_p, c_p = np.percentile(prices, 20), np.percentile(prices, 50), np.percentile(prices, 80)
            
            # Log thresholds for analysis
            p2p_fin.at[idx, 'Price_Floor_20'] = f_p
            p2p_fin.at[idx, 'Price_Median_50'] = m_p
            p2p_fin.at[idx, 'Price_Ceil_80'] = c_p
            
            # Update User Demand via Battery
            row[target], p2p_fin.at[idx, f'{target}_SoC'] = batt.optimize_demand(row[target], tou, f_p, c_p, m_p)
            p2p_fin.at[idx, f'{target}_Final'] = row[target]

        # 3. Community State (Post-Flexibility)
        net = sum(row[a] for a in agent_ids)
        state = 'Shortage' if net > 1e-9 else ('Surplus' if net < -1e-9 else 'Balance')
        counts[state] += 1
        p2p_fin.at[idx, 'State'] = state

        # 4. P2P Matching Logic
        if tou <= fit: # Rationality Guard
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
                
                # Financials
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
            
            # Residual Grid Settlement
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

    # 5. Reporting
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
    
    print(f"Community Savings: {tots['Savings %']}% | Peer Trade: {tots['Peer Trade %']}%")

if __name__ == "__main__":
    start = time.time()
    run_energy_market_simulation('data/orderbook.csv', 'data/alphas.csv', 'orderbook_results/detailed_transactions.csv', 'orderbook_results/summary_transactions.csv')
    print(f"Runtime: {time.time() - start:.4f}s")