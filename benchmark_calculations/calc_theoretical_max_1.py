import pandas as pd
import numpy as np

def calculate_pure_local_max():
    print("--- Calculating 'Pure Local' Virtual Battery Upper Bounds ---")
    
    # 1. Load Data
    try:
        df = pd.read_csv('data/orderbook.csv')
    except FileNotFoundError:
        print("Error: 'orderbook.csv' not found.")
        return

    # Identify agents
    agent_ids = [c for c in df.columns if c not in [
        'timestamp', 'time_year_sin', 'time_year_cos', 
        'time_day_sin', 'time_day_cos', 'is_working_day', 
        'import_price', 'export_price', 'spread', 'net_community'
    ]]
    a1_col = '1_Prosumer'
    other_agents_cols = [c for c in agent_ids if c != a1_col]
    
    tou = df['import_price'].values
    fit = df['export_price'].values
    midpoint = (tou + fit) / 2.0
    
    all_data = df[agent_ids].values
    a1_data = df[a1_col].values
    others_data = df[other_agents_cols].sum(axis=1).values

    # ==========================================
    # 1. MAX PEER TRADE % (Physical Overlap Limit)
    # ==========================================
    total_demand = all_data[all_data > 0].sum()
    total_supply = abs(all_data[all_data < 0].sum())
    
    max_physical_trade = min(total_demand, total_supply)
    max_pt_percent = (max_physical_trade * 2) / (total_demand + total_supply) * 100

    # ==========================================
    # 2. MAX COMMUNITY SAVINGS % (Pure Local VB)
    # ==========================================
    # Baseline Costs
    comm_base_costs = (all_data[all_data > 0] * np.broadcast_to(tou[:, None], all_data.shape)[all_data > 0]).sum()
    comm_base_revs = (abs(all_data[all_data < 0]) * np.broadcast_to(fit[:, None], all_data.shape)[all_data < 0]).sum()
    comm_baseline_net = comm_base_costs - comm_base_revs

    comm_soc = 0.0
    comm_vb_cost = 0.0
    net_comm_array = all_data.sum(axis=1)

    for t in range(len(df)):
        net_load = net_comm_array[t]
        
        if net_load < 0:
            # Surplus: Store in Virtual Battery (NO selling to grid)
            comm_soc += abs(net_load)
        elif net_load > 0:
            # Shortage: Draw from Virtual Battery
            if comm_soc >= net_load:
                comm_soc -= net_load
            else:
                # VB is empty. Buy strictly what is needed from grid.
                grid_buy = net_load - comm_soc
                comm_soc = 0.0
                comm_vb_cost += grid_buy * tou[t]

    # Sell leftover infinite battery at the end of 2 years to grid
    comm_vb_cost -= comm_soc * np.mean(fit)
    max_comm_savings = ((comm_baseline_net - comm_vb_cost) / abs(comm_baseline_net)) * 100

    # ==========================================
    # 3. MAX AGENT 1 SAVINGS % (Pure Local Dictator)
    # ==========================================
    # Agent 1 Baseline
    a1_base_costs = (a1_data[a1_data > 0] * tou[a1_data > 0]).sum()
    a1_base_revs = (abs(a1_data[a1_data < 0]) * fit[a1_data < 0]).sum()
    a1_baseline_net = a1_base_costs - a1_base_revs

    a1_soc = 0.0
    a1_cost = 0.0

    for t in range(len(df)):
        a1_load = a1_data[t]
        others_load = others_data[t]
        mid_p = midpoint[t]
        
        # Step A: Store own solar
        if a1_load < 0:
            a1_soc += abs(a1_load)
            a1_load = 0.0
            
        # Step B: Buy neighbors' surplus (Store it, don't immediately sell)
        if others_load < 0:
            surplus = abs(others_load)
            a1_soc += surplus
            a1_cost += surplus * mid_p
            others_load = 0.0
            
        # Step C: Meet own demand from battery
        if a1_load > 0:
            used = min(a1_load, a1_soc)
            a1_soc -= used
            a1_load -= used
            if a1_load > 0:
                a1_cost += a1_load * tou[t] # Grid buy
                
        # Step D: Sell remaining battery to neighbors' demand
        if others_load > 0:
            sold = min(others_load, a1_soc)
            a1_soc -= sold
            a1_cost -= sold * mid_p # Revenue

    a1_cost -= a1_soc * np.mean(fit)
    max_a1_savings = ((a1_baseline_net - a1_cost) / abs(a1_baseline_net)) * 100

    # ==========================================
    # PRINT RESULTS
    # ==========================================
    print("\n" + "="*50)
    print(" 'PURE LOCAL' VIRTUAL BATTERY BOUNDS")
    print("="*50)
    print(f"1. Max Peer Trade %:       {max_pt_percent:.2f}%")
    print(f"2. Max Community Savings:  {max_comm_savings:.2f}%")
    print(f"3. Max Agent 1 Savings:    {max_a1_savings:.2f}%")
    print("="*50)

if __name__ == "__main__":
    calculate_pure_local_max()