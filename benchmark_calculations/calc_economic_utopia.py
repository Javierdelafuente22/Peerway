import pandas as pd
import numpy as np

def calculate_economic_utopia():
    print("--- Calculating Economic Utopia (100% P2P at Midpoint) ---")
    
    # 1. Load Data
    try:
        df = pd.read_csv('data/orderbook.csv')
    except FileNotFoundError:
        print("Error: 'orderbook.csv' not found. Run the case generator first.")
        return

    # Identify agents
    agent_ids = [c for c in df.columns if c not in [
        'timestamp', 'time_year_sin', 'time_year_cos', 
        'time_day_sin', 'time_day_cos', 'is_working_day', 
        'import_price', 'export_price', 'spread', 'net_community'
    ]]
    a1_col = '1_Prosumer'
    
    tou = df['import_price'].values
    fit = df['export_price'].values
    midpoint = (tou + fit) / 2.0
    
    all_data = df[agent_ids].values
    a1_data = df[a1_col].values

    # ==========================================
    # BASELINE (Grid Only)
    # ==========================================
    # Community Baseline Net Cost
    comm_base_costs = (all_data[all_data > 0] * np.broadcast_to(tou[:, None], all_data.shape)[all_data > 0]).sum()
    comm_base_revs = (abs(all_data[all_data < 0]) * np.broadcast_to(fit[:, None], all_data.shape)[all_data < 0]).sum()
    comm_baseline_net = comm_base_costs - comm_base_revs

    # Agent 1 Baseline Net Cost
    a1_base_costs = (a1_data[a1_data > 0] * tou[a1_data > 0]).sum()
    a1_base_revs = (abs(a1_data[a1_data < 0]) * fit[a1_data < 0]).sum()
    a1_baseline_net = a1_base_costs - a1_base_revs

    # ==========================================
    # ECONOMIC UTOPIA (100% Volume at Midpoint)
    # ==========================================
    # In this utopia, every kWh of demand pays the midpoint, and every kWh of supply earns the midpoint.
    
    # Community Utopia Net Cost
    comm_utopia_costs = (all_data[all_data > 0] * np.broadcast_to(midpoint[:, None], all_data.shape)[all_data > 0]).sum()
    comm_utopia_revs = (abs(all_data[all_data < 0]) * np.broadcast_to(midpoint[:, None], all_data.shape)[all_data < 0]).sum()
    comm_utopia_net = comm_utopia_costs - comm_utopia_revs
    
    comm_utopia_savings = ((comm_baseline_net - comm_utopia_net) / abs(comm_baseline_net)) * 100

    # Agent 1 Utopia Net Cost
    a1_utopia_costs = (a1_data[a1_data > 0] * midpoint[a1_data > 0]).sum()
    a1_utopia_revs = (abs(a1_data[a1_data < 0]) * midpoint[a1_data < 0]).sum()
    a1_utopia_net = a1_utopia_costs - a1_utopia_revs
    
    a1_utopia_savings = ((a1_baseline_net - a1_utopia_net) / abs(a1_baseline_net)) * 100

    # ==========================================
    # PRINT RESULTS
    # ==========================================
    print("\n" + "="*50)
    print(" THE 'ECONOMIC UTOPIA' BOUNDS")
    print(" (100% Balanced, All volume cleared at Midpoint)")
    print("="*50)
    print(f"1. Max Peer Trade %:       100.00% (By Definition)")
    print(f"2. Max Community Savings:  {comm_utopia_savings:.2f}%")
    print(f"3. Max Agent 1 Savings:    {a1_utopia_savings:.2f}%")
    print("="*50)

if __name__ == "__main__":
    calculate_economic_utopia()