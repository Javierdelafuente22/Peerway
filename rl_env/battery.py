"""
Battery model for Tesla Powerwall 3 (normalised units).

Physics convention (matches LP benchmark):
    - Charging:    SoC increases by charge_amount * efficiency
                   Demand increases by charge_amount (drawn from market)
    - Discharging: SoC decreases by discharge_amount
                   Demand decreases by discharge_amount * efficiency (delivered to market)
    
    Round-trip efficiency: η² ≈ 0.9025 (for η = 0.95)
"""

import numpy as np


class Battery:
    def __init__(self, capacity=1.0, max_rate=0.4, efficiency=0.95, initial_soc=0.0):
        self.capacity = capacity
        self.max_rate = max_rate
        self.efficiency = efficiency
        self.initial_soc = initial_soc
        self.soc = initial_soc

    def reset(self):
        """Reset battery to initial SoC (called at start of each episode)."""
        self.soc = self.initial_soc
        return self.soc

    def apply_action(self, action_power):
        """
        Apply a charge/discharge action, respecting physical constraints.
        
        Args:
            action_power: Desired power. Positive = charge, negative = discharge.
                          e.g., +0.4 = charge at full rate, -0.2 = discharge at half rate
        
        Returns:
            demand_delta: Change in net demand from the agent's perspective.
                          Positive = agent draws more from market (charging).
                          Negative = agent supplies more to market (discharging).
            new_soc: Updated state of charge.
        """
        if action_power > 0:
            # CHARGING: agent draws power from market, stores in battery
            # Clip by: max rate, available capacity (accounting for efficiency)
            max_charge_by_capacity = (self.capacity - self.soc) / self.efficiency
            actual_charge = min(action_power, self.max_rate, max(0, max_charge_by_capacity))
            
            self.soc += actual_charge * self.efficiency
            demand_delta = actual_charge  # Agent draws this much extra from market

        elif action_power < 0:
            # DISCHARGING: battery releases power, agent supplies to market
            # Clip by: max rate, available energy in battery
            desired_discharge = abs(action_power)
            max_discharge_by_soc = self.soc  # Can't discharge more than what's stored
            actual_discharge = min(desired_discharge, self.max_rate, max(0, max_discharge_by_soc))
            
            self.soc -= actual_discharge
            demand_delta = -(actual_discharge * self.efficiency)  # Delivered to market (less due to efficiency)

        else:
            # DO NOTHING
            demand_delta = 0.0

        # Safety clamp (floating point edge cases)
        self.soc = np.clip(self.soc, 0.0, self.capacity)
        
        return demand_delta, self.soc
