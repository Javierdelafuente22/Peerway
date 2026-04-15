"""
Simplified orderbook clearing for the RL environment.

Since price is fixed at midpoint and 1_Prosumer has priority,
we only need to determine how much trades P2P vs grid.

This produces identical costs for 1_Prosumer as the full orderbook
when all alphas are 0.5.
"""

import numpy as np


def clear_market_for_agent(modified_demand, others_demands, import_price, export_price):
    """
    Compute the cost for our target agent after market clearing.
    
    Args:
        modified_demand:  1_Prosumer's net demand after battery action.
                          Positive = buying, negative = selling.
        others_demands:   Array of other agents' demands (from dataset, fixed).
                          Positive = buying, negative = selling.
        import_price:     Grid buy price (ToU).
        export_price:     Grid sell price (FiT).
    
    Returns:
        agent_cost:       Net cost for our agent (negative = revenue/profit).
        p2p_volume:       Amount traded P2P by our agent (absolute kWh).
        grid_volume:      Amount traded with grid by our agent (absolute kWh).
    """
    midpoint = (import_price + export_price) / 2.0
    
    # No arbitrage check: if import <= export, no P2P benefit, all goes to grid
    if import_price <= export_price:
        if modified_demand > 0:
            return modified_demand * import_price, 0.0, modified_demand
        elif modified_demand < 0:
            return -(abs(modified_demand) * export_price), 0.0, abs(modified_demand)
        else:
            return 0.0, 0.0, 0.0
    
    # Available P2P counterparties from other agents
    others_supply = np.sum(np.abs(others_demands[others_demands < 0]))  # Total selling
    others_demand = np.sum(others_demands[others_demands > 0])           # Total buying
    
    if modified_demand > 0:
        # Agent is BUYING
        p2p_bought = min(modified_demand, others_supply)
        grid_bought = modified_demand - p2p_bought
        agent_cost = p2p_bought * midpoint + grid_bought * import_price
        return agent_cost, p2p_bought, grid_bought
        
    elif modified_demand < 0:
        # Agent is SELLING
        sell_amount = abs(modified_demand)
        p2p_sold = min(sell_amount, others_demand)
        grid_sold = sell_amount - p2p_sold
        agent_cost = -(p2p_sold * midpoint + grid_sold * export_price)
        return agent_cost, p2p_sold, grid_sold
        
    else:
        return 0.0, 0.0, 0.0


def compute_baseline_cost(raw_demand, import_price, export_price):
    """
    What the agent would pay/earn with NO battery and NO P2P.
    This is the reference point for computing savings.
    
    Args:
        raw_demand:   Original 1_Prosumer demand (before battery).
        import_price: Grid buy price (ToU).
        export_price: Grid sell price (FiT).
    
    Returns:
        baseline_cost: Cost at pure grid prices.
    """
    if raw_demand > 0:
        return raw_demand * import_price
    elif raw_demand < 0:
        return -(abs(raw_demand) * export_price)
    else:
        return 0.0
