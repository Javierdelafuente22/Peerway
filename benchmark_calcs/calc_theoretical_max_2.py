import pandas as pd
import numpy as np

def calculate_true_theoretical_max():
    print("--- Calculating True Mathematical Upper Bounds ---")
    
    df = pd.read_csv('data/orderbook.csv')
    
    # 1. Identify Agents
    agent_ids = [c for c in df.columns if c not in [
        'timestamp', 'time_year_sin', 'time_year_cos', 
        'time_day_sin', 'time_day_cos', 'is_working_day', 
        'import_price', 'export_price', 'spread', 'net_community'
    ]]
    a1_col = '1_Prosumer'
    
    tou = df['import_price'].values
    fit = df['export_price'].values
    
    all_data = df[agent_ids].values
    a1_data = df[a1_col].values

    # ==========================================
    # 1. MAX PEER TRADE % (Orderbook Accounting)
    # ==========================================
    total_demand = all_data[all_data > 0].sum()
    total_supply = abs(all_data[all_data < 0].sum())
    
    # Physical maximum that can be traded is the smaller of the two buckets
    max_physical_trade = min(total_demand, total_supply)
    
    # Applying the Orderbook's (2 * P2P) / (P2P + Grid) formula:
    max_pt_percent = (max_physical_trade * 2) / (total_demand + total_supply) * 100

    # ==========================================
    # 2. MAX COMMUNITY SAVINGS %
    # ==========================================
    # Orderbook Baseline: Costs are negative, revenues are positive
    comm_base_costs = -1 * (all_data[all_data > 0] * np.broadcast_to(tou[:, None], all_data.shape)[all_data > 0]).sum()
    comm_base_revs = (abs(all_data[all_data < 0]) * np.broadcast_to(fit[:, None], all_data.shape)[all_data < 0]).sum()
    comm_baseline_net = comm_base_costs + comm_base_revs # Will be a negative number overall

    # God-Mode Community: The community pools all energy perfectly over 2 years.
    # They only buy the absolute net difference from the grid.
    if total_demand > total_supply:
        # Community is net negative. Assume they buy the deficit at the minimum ToU price
        net_deficit = total_demand - total_supply
        comm_max_net = -1 * (net_deficit * tou.min())
    else:
        # Community is net positive. Assume they sell the surplus at the max FiT price
        net_surplus = total_supply - total_demand
        comm_max_net = net_surplus * fit.max()

    max_comm_savings = ((comm_max_net - comm_baseline_net) / abs(comm_baseline_net)) * 100

    # ==========================================
    # 3. MAX AGENT 1 SAVINGS % (The Dictator)
    # ==========================================
    # Agent 1 Baseline
    a1_base_costs = -1 * (a1_data[a1_data > 0] * tou[a1_data > 0]).sum()
    a1_base_revs = (abs(a1_data[a1_data < 0]) * fit[a1_data < 0]).sum()
    a1_baseline_net = a1_base_costs + a1_base_revs

    a1_total_demand = a1_data[a1_data > 0].sum()
    a1_total_supply = abs(a1_data[a1_data < 0].sum())
    
    # Calculate neighbors' total energy
    others_data = df[[c for c in agent_ids if c != a1_col]].values
    others_demand = others_data[others_data > 0].sum()
    others_supply = abs(others_data[others_data < 0].sum())

    a1_max_net = 0.0
    
    # God-Mode Agent 1 Logic:
    # 1. perfectly offset own demand with own supply
    a1_net_energy = a1_total_demand - a1_total_supply
    
    if a1_net_energy > 0:
        # Agent 1 needs energy. It buys from neighbors at FiT (cheapest possible). 
        # If neighbors run out, it buys from grid at min(ToU)
        bought_from_neighbors = min(a1_net_energy, others_supply)
        bought_from_grid = a1_net_energy - bought_from_neighbors
        a1_max_net = -1 * (bought_from_neighbors * fit.min() + bought_from_grid * tou.min())
    else:
        # Agent 1 has surplus. It sells to neighbors at ToU (highest possible).
        # If neighbors are full, it sells to grid at max(FiT)
        surplus = abs(a1_net_energy)
        sold_to_neighbors = min(surplus, others_demand)
        sold_to_grid = surplus - sold_to_neighbors
        a1_max_net = (sold_to_neighbors * tou.max() + sold_to_grid * fit.max())

    max_a1_savings = ((a1_max_net - a1_baseline_net) / abs(a1_baseline_net)) * 100

    # ==========================================
    # PRINT RESULTS
    # ==========================================
    print("\n" + "="*50)
    print(" TRUE MATHEMATICAL UPPER BOUNDS")
    print("="*50)
    print(f"1. Max Peer Trade %:       {max_pt_percent:.2f}%")
    print(f"2. Max Community Savings:  {max_comm_savings:.2f}%")
    print(f"3. Max Agent 1 Savings:    {max_a1_savings:.2f}%")
    print("="*50)

if __name__ == "__main__":
    calculate_true_theoretical_max()