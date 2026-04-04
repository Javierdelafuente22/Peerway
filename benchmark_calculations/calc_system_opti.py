import pandas as pd
import numpy as np
import pulp

def calculate_multi_agent_community_optimum():
    print("--- Calculating Multi-Agent Coordinated Community Optimum ---")
    
    df = pd.read_csv('data/orderbook.csv')
    agent_ids = [c for c in df.columns if c not in [
        'timestamp', 'time_year_sin', 'time_year_cos', 'is_working_day', 
        'import_price', 'export_price', 'spread', 'net_community'
    ]]
    
    tou, fit = df['import_price'].values, df['export_price'].values
    T = len(df)
    
    # HARDWARE SPECS (Applied to ALL 10 agents)
    BATT_CAPACITY, BATT_POWER, EFFICIENCY = 1.0, 0.4, 0.95

    # 1. SETUP THE GLOBAL PROBLEM
    prob = pulp.LpProblem("Community_Cooperative_Optimum", pulp.LpMinimize)

    # 2. DECISION VARIABLES (Nested: [agent][time])
    soc = pulp.LpVariable.dicts("SOC", (agent_ids, range(T)), 0, BATT_CAPACITY)
    p_charge = pulp.LpVariable.dicts("Charge", (agent_ids, range(T)), 0, BATT_POWER)
    p_discharge = pulp.LpVariable.dicts("Discharge", (agent_ids, range(T)), 0, BATT_POWER)
    
    # Community-level grid variables
    grid_buy = pulp.LpVariable.dicts("CommGridBuy", range(T), 0)
    grid_sell = pulp.LpVariable.dicts("CommGridSell", range(T), 0)

    # 3. OBJECTIVE: Minimize Total Community Bill
    prob += pulp.lpSum([
        grid_buy[t] * tou[t] - grid_sell[t] * fit[t]
        for t in range(T)
    ])

    # 4. CONSTRAINTS
    for t in range(T):
        # A. Battery Physics for EVERY agent
        for a in agent_ids:
            if t == 0:
                prob += soc[a][t] == (p_charge[a][t] * EFFICIENCY) - (p_discharge[a][t] / EFFICIENCY)
            else:
                prob += soc[a][t] == soc[a][t-1] + (p_charge[a][t] * EFFICIENCY) - (p_discharge[a][t] / EFFICIENCY)

        # B. Global Energy Balance
        # Total Load + Total Charge - Total Discharge = Total Grid Buy - Total Grid Sell
        total_load_at_t = sum(df[a].values[t] for a in agent_ids)
        total_charge_at_t = pulp.lpSum([p_charge[a][t] for a in agent_ids])
        total_discharge_at_t = pulp.lpSum([p_discharge[a][t] for a in agent_ids])
        
        prob += total_load_at_t + total_charge_at_t - total_discharge_at_t == grid_buy[t] - grid_sell[t]

    print("Solving Global Optimization... (This will take longer as there are 10x more variables)")
    prob.solve(pulp.PULP_CBC_CMD(msg=0))

    # 5. CALCULATE KPIs
    # Baseline: No P2P, No Batteries (Everyone for themselves)
    comm_baseline_cost = 0
    for a in agent_ids:
        load = df[a].values
        comm_baseline_cost += (load[load > 0]*tou[load > 0]).sum() - (np.abs(load[load < 0])*fit[load < 0]).sum()

    opt_comm_cost = pulp.value(prob.objective)
    comm_savings_pct = ((comm_baseline_cost - opt_comm_cost) / abs(comm_baseline_cost)) * 100

    # Peer Trade Calculation: 
    # In a coordinated system, P2P is the amount of local generation used locally.
    total_gen = abs(df[agent_ids].clip(upper=0).sum().sum())
    total_dem = df[agent_ids].clip(lower=0).sum().sum()
    
    # Energy that didn't come from or go to the grid was traded peer-to-peer
    total_grid_buy = sum(pulp.value(grid_buy[t]) for t in range(T))
    total_grid_sell = sum(pulp.value(grid_sell[t]) for t in range(T))
    
    # Total Community Peer Trade Volume
    # Formula: (Total Demand + Total Supply - Total Grid Activity) / 2
    # Because each trade is counted as 1 unit for the buyer and 1 for the seller
    p2p_vol = (total_dem + total_gen - (total_grid_buy + total_grid_sell)) 
    pt_pct = (p2p_vol / (total_dem + total_gen)) * 100

    print("\n" + "="*55)
    print(" ULTIMATE COOPERATIVE UPPER BOUND (10 Batteries)")
    print("="*55)
    print(f"% Peer Trades:      {pt_pct:.2f}%")
    print(f"% Community Saving: {comm_savings_pct:.2f}%")
    print(f"Total Comm. Cost:   {opt_comm_cost:.2f}")
    print("="*55)

if __name__ == "__main__":
    calculate_multi_agent_community_optimum()