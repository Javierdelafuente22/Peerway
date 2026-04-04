# battery_alg_template.py

class BaseBattery:
    def __init__(self, max_rate=0.4, efficiency=0.95, min_soc=0.0, max_soc=1.0):
        """Initialize the physical constraints of the battery."""
        self.max_rate = max_rate
        self.efficiency = efficiency
        self.min_soc = min_soc
        self.max_soc = max_soc
        self.soc = min_soc 

    def optimize_demand(self, raw_demand, current_price, floor_p, ceil_p, median_p):
        """
        TEMPLATE: Replace this logic with your new algorithm.
        
        Inputs:
        - raw_demand (float): The user's original demand (negative for surplus, positive for shortage).
        - current_price (float): The current grid import price.
        - floor_p, ceil_p, median_p (float or None): 24h rolling price percentiles.
        
        Returns:
        - tuple: (final_demand, current_soc)
        """
        # --- YOUR CUSTOM ALGORITHM GOES HERE ---
        
        # Example: A "Dumb" battery that does absolutely nothing
        final_demand = raw_demand
        
        # ---------------------------------------
        
        return final_demand, self.soc