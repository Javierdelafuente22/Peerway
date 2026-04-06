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
    
    # Target Agent 1
    a1_col = '1_Prosumer'
    
    tou, fit = df['import_price'].values, df['export_price'].values
    midpoint = (tou + fit) / 2.0
    T = len(df)
    
    # HARDWARE SPECS (Applied to ALL 10 agents)
    BATT_CAPACITY, BATT_POWER, EFFICIENCY = 1.0, 0.4, 0.95

    # 1. SETUP THE GLOBAL PROBLEM
    prob = pulp.LpProblem("Community_Cooperative_Optimum", pulp.LpMinimize)

    # 2. DECISION VARIABLES
    soc = pulp.LpVariable.dicts("SOC", (agent_ids, range(T)), 0, BATT_CAPACITY)
    p_charge = pulp.LpVariable.dicts("Charge", (agent_ids, range(T)), 0, BATT_POWER)
    p_discharge = pulp.LpVariable.dicts("Discharge", (agent_ids, range(T)), 0, BATT_POWER)
    
    grid_buy = pulp.LpVariable.dicts("CommGridBuy", range(T), 0)
    grid_sell = pulp.LpVariable.dicts("CommGridSell", range(T), 0)

    # 3. OBJECTIVE: Minimize Total Community Bill
    prob += pulp.lpSum([
        grid_buy[t] * tou[t] - grid_sell[t] * fit[t]
        for t in range(T)
    ])

    # 4. CONSTRAINTS
    for t in range(T):
        # Battery Physics for EVERY agent
        for a in agent_ids:
            if t == 0:
                prob += soc[a][t] == (p_charge[a][t] * EFFICIENCY) - (p_discharge[a][t] / EFFICIENCY)
            else:
                prob += soc[a][t] == soc[a][t-1] + (p_charge[a][t] * EFFICIENCY) - (p_discharge[a][t] / EFFICIENCY)

        # FIXED: Define total_net_load properly
        total_load_at_t = sum(df[a].values[t] for a in agent_ids)
        total_charge_at_t = pulp.lpSum([p_charge[a][t] for a in agent_ids])
        total_discharge_at_t = pulp.lpSum([p_discharge[a][t] for a in agent_ids])
        
        # Constraint: Net Demand = Grid Activity
        prob += total_load_at_t + total_charge_at_t - total_discharge_at_t == grid_buy[t] - grid_sell[t]

    print("Solving Global Optimisation...")
    prob.solve(pulp.PULP_CBC_CMD(msg=0))

    # 5. CALCULATE KPIs (COMMUNITY)
    comm_baseline_cost = 0
    for a in agent_ids:
        load = df[a].values
        comm_baseline_cost += (load[load > 0]*tou[load > 0]).sum() - (np.abs(load[load < 0])*fit[load < 0]).sum()

    opt_comm_cost = pulp.value(prob.objective)
    comm_savings_pct = ((comm_baseline_cost - opt_comm_cost) / abs(comm_baseline_cost)) * 100

    # 6. CALCULATE KPIs (AGENT 1 INDIVIDUAL)
    # Baseline for Agent 1 (Grid-only, no battery)
    a1_load = df[a1_col].values
    a1_base_cost = (a1_load[a1_load > 0]*tou[a1_load > 0]).sum() - (np.abs(a1_load[a1_load < 0])*fit[a1_load < 0]).sum()
    
    # Optimized Personal Cost for Agent 1 in Cooperative Mode
    a1_opt_cost = 0
    for t in range(T):
        # Personal net demand for Agent 1 after their battery's contribution
        a1_net = a1_load[t] + pulp.value(p_charge[a1_col][t]) - pulp.value(p_discharge[a1_col][t])
        
        c_buy = pulp.value(grid_buy[t])
        c_sell = pulp.value(grid_sell[t])
        
        # Calculate total absolute net demand of all agents to find Agent 1's share
        if a1_net > 0: # Agent 1 is a buyer
            total_community_demand = sum(max(0, df[a].values[t] + pulp.value(p_charge[a][t]) - pulp.value(p_discharge[a][t])) for a in agent_ids)
            # What % of the community's demand was satisfied by neighbors?
            p2p_ratio = (total_community_demand - c_buy) / total_community_demand if total_community_demand > 1e-9 else 0
            a1_opt_cost += a1_net * (p2p_ratio * midpoint[t] + (1 - p2p_ratio) * tou[t])
        elif a1_net < 0: # Agent 1 is a seller
            total_community_supply = sum(max(0, -(df[a].values[t] + pulp.value(p_charge[a][t]) - pulp.value(p_discharge[a][t]))) for a in agent_ids)
            # What % of the community's supply was bought by neighbors?
            p2p_ratio = (total_community_supply - c_sell) / total_community_supply if total_community_supply > 1e-9 else 0
            a1_opt_cost -= abs(a1_net) * (p2p_ratio * midpoint[t] + (1 - p2p_ratio) * fit[t])

    a1_savings_pct = ((a1_base_cost - a1_opt_cost) / abs(a1_base_cost)) * 100

    # Peer Trade Calculation
    total_gen = abs(df[agent_ids].clip(upper=0).sum().sum())
    total_dem = df[agent_ids].clip(lower=0).sum().sum()
    total_grid_buy = sum(pulp.value(grid_buy[t]) for t in range(T))
    total_grid_sell = sum(pulp.value(grid_sell[t]) for t in range(T))
    
    # In a coordinated system, P2P is the volume that never touched the grid
    p2p_vol = (total_dem + total_gen - (total_grid_buy + total_grid_sell)) 
    pt_pct = (p2p_vol / (total_dem + total_gen)) * 100

    print("\n" + "="*55)
    print("COOPERATIVE UPPER BOUND (10 Batteries)")
    print("="*55)
    print(f"% Peer Trades:      {pt_pct:.2f}%")
    print(f"% Community Saving: {comm_savings_pct:.2f}%")
    print(f"% Agent 1 Saving:   {a1_savings_pct:.2f}%")
    print("="*55)

if __name__ == "__main__":
    calculate_multi_agent_community_optimum()