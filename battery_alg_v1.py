# battery_alg_1.py

class Battery_v1:
    def __init__(self, max_rate=0.4, efficiency=0.95, min_soc=0.0, max_soc=1.0):
        self.max_rate = max_rate
        self.efficiency = efficiency
        self.min_soc = min_soc
        self.max_soc = max_soc
        self.soc = min_soc 

    def optimize_demand(self, raw_demand, current_price, floor_p, ceil_p, median_p):
        rem_rate = self.max_rate
        
        # Priority 1: Self-Consumption / Surplus Capture
        if raw_demand < 0:
            charge = min(abs(raw_demand), rem_rate, (self.max_soc - self.soc) / self.efficiency)
            self.soc += charge * self.efficiency
            rem_rate -= charge
            raw_demand += charge
            
        elif raw_demand > 0:
            if median_p is not None and (current_price >= median_p or current_price >= ceil_p):
                available = self.soc - self.min_soc
                discharge = min(raw_demand, rem_rate, available)
                self.soc -= discharge
                rem_rate -= discharge
                raw_demand -= discharge
            
        # Priority 2: Market Arbitrage
        if floor_p is not None and rem_rate > 0:
            if current_price <= floor_p and self.soc < self.max_soc:
                charge = min(rem_rate, (self.max_soc - self.soc) / self.efficiency)
                self.soc += charge * self.efficiency
                raw_demand += charge
            elif current_price >= ceil_p and self.soc > self.min_soc:
                available = self.soc - self.min_soc
                discharge = min(rem_rate, available)
                self.soc -= discharge
                raw_demand -= discharge
                
        return raw_demand, self.soc