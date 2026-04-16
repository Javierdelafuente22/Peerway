"""
P2P Energy Trading Gymnasium Environment.

The agent controls a battery for 1_Prosumer, deciding when to charge/discharge
to minimise energy costs through a combination of P2P trading and grid arbitrage.

Episode: 1 day (24 hourly steps), SoC resets to 0 at start.
State:   11 continuous features (demand, SoC, prices, time, community).
Actions: 5 discrete (do nothing, charge half/full, discharge half/full).
Reward:  Scaled cost savings vs grid-only baseline.
"""

import gymnasium as gym
from gymnasium import spaces
import numpy as np
import pandas as pd

from rl_env.battery import Battery
from rl_env.rl_orderbook_simp import clear_market_for_agent


# ---------- Action mapping ----------
# Maps discrete action index to desired charge/discharge power
# Simplified 3-action space for first training run
ACTION_MAP = {
    0:  0.0,    # Do nothing
    1:  0.4,    # Charge full rate
    2: -0.4,    # Discharge full rate
}

# ---------- State feature columns (from dataset) ----------
MARKET_FEATURES = [
    'import_price', 'export_price', 'spread', 'net_community',
    'time_day_sin', 'time_day_cos', 'time_year_sin', 'time_year_cos',
    'is_working_day'
]

TARGET_AGENT = '1_Prosumer'
OTHER_AGENTS = ['2_Prosumer', '3_Prosumer', '4_Prosumer', '5_Prosumer',
                '6_Buyer', '7_Buyer', '8_Seller', '9_Seller', '10_Seller']


class P2PEnergyTradingEnv(gym.Env):
    """
    Gymnasium environment for P2P energy trading with battery optimisation.
    """
    metadata = {"render_modes": []}
    
    def __init__(self, df, reward_scale=10.0, episode_length=24):
        """
        Args:
            df:             DataFrame with full dataset (already filtered to train or test).
            reward_scale:   Multiplier for reward signal.
            episode_length: Steps per episode (24 = 1 day).
        """
        super().__init__()
        
        self.df = df.reset_index(drop=True)
        self.reward_scale = reward_scale
        self.episode_length = episode_length
        
        # Precompute numpy arrays for fast access during training
        self.raw_demands = self.df[TARGET_AGENT].values.astype(np.float32)
        self.market_features = self.df[MARKET_FEATURES].values.astype(np.float32)
        self.import_prices = self.df['import_price'].values.astype(np.float32)
        self.export_prices = self.df['export_price'].values.astype(np.float32)
        self.others_demands = self.df[OTHER_AGENTS].values.astype(np.float32)
        
        # Identify valid episode start indices (each episode = 24 consecutive hours)
        # Episodes start at midnight (step 0, 24, 48, ...) to represent full days
        total_rows = len(self.df)
        self.episode_starts = list(range(0, total_rows - episode_length + 1, episode_length))
        
        if len(self.episode_starts) == 0:
            raise ValueError(f"Dataset too small ({total_rows} rows) for episode_length={episode_length}")
        
        # Battery
        self.battery = Battery(capacity=1.0, max_rate=0.4, efficiency=0.95, initial_soc=0.0)
        
        # Action space: 5 discrete actions
        self.action_space = spaces.Discrete(len(ACTION_MAP))
        
        # Observation space: 11 continuous features
        # [net_demand, soc, import_price, export_price, spread, net_community,
        #  time_day_sin, time_day_cos, time_year_sin, time_year_cos, is_working_day]
        self.observation_space = spaces.Box(
            low=-1.5, high=1.5,  # Slightly wider than data range for safety
            shape=(11,),
            dtype=np.float32
        )
        
        # Internal state
        self.current_episode_start = 0
        self.current_step = 0
        self.episode_idx = 0
        
    def reset(self, seed=None, options=None):
        """Reset environment to start of a new episode (new day)."""
        super().reset(seed=seed)
        
        # Pick the next episode sequentially (chronological training)
        self.current_episode_start = self.episode_starts[self.episode_idx % len(self.episode_starts)]
        self.episode_idx += 1
        
        self.current_step = 0
        self.battery.reset()
        
        obs = self._get_observation()
        info = {}
        return obs, info
    
    def step(self, action):
        """
        Execute one trading step (1 hour).
        
        Returns: observation, reward, terminated, truncated, info
        """
        global_idx = self.current_episode_start + self.current_step
        
        # 1. Read market data for this timestep
        raw_demand = float(self.raw_demands[global_idx])
        import_price = float(self.import_prices[global_idx])
        export_price = float(self.export_prices[global_idx])
        others = self.others_demands[global_idx]
        
        # 2. Apply battery action
        action_power = ACTION_MAP[action]
        demand_delta, new_soc = self.battery.apply_action(action_power)
        modified_demand = raw_demand + demand_delta
        
        # 3. Clear market TWICE for reward computation:
        #    (a) WITHOUT battery action -- counterfactual "what would have happened"
        #    (b) WITH battery action    -- what actually happened
        # The reward is the difference, isolating ONLY the battery's contribution.
        # Both clearings use the same P2P market, so exogenous P2P effects cancel out.
        cost_no_battery, _, _ = clear_market_for_agent(
            raw_demand, others, import_price, export_price
        )
        actual_cost, p2p_vol, grid_vol = clear_market_for_agent(
            modified_demand, others, import_price, export_price
        )
        
        # 4. Reward = pure battery contribution this step
        # Positive when the battery action reduced cost vs doing nothing.
        # Negative when the battery action increased cost (e.g., charging when expensive).
        # This removes all exogenous noise from demand/price/community variation.
        raw_reward = cost_no_battery - actual_cost
        reward = float(raw_reward * self.reward_scale)
        
        # 6. Advance step
        self.current_step += 1
        # Episode ends due to TIME LIMIT (day ended), not task completion.
        # Under Gymnasium API: time limits are `truncated`, goal-reached is `terminated`.
        # This distinction is critical for PPO: `terminated=True` tells SB3 the terminal
        # value is 0 (no bootstrap), which destroys GAE advantage estimation for episodic
        # daily tasks. `truncated=True` correctly tells SB3 to bootstrap the value.
        terminated = False
        truncated = self.current_step >= self.episode_length
        
        # 7. Build next observation
        # On truncation (day ended), we return the last valid observation of the day
        # (current step's observation, before advancing). SB3's DummyVecEnv will store
        # this in info['terminal_observation'] for value bootstrapping before reset.
        done = terminated or truncated
        if done:
            # Use the current (final) step's observation for bootstrapping
            obs = np.zeros(11, dtype=np.float32)
            obs[0] = raw_demand
            obs[1] = new_soc
            obs[2:11] = self.market_features[global_idx]
        else:
            obs = self._get_observation()
        
        # 8. Info dict for logging/reporting
        info = {
            'raw_demand': raw_demand,
            'modified_demand': modified_demand,
            'soc': new_soc,
            'actual_cost': actual_cost,
            'cost_no_battery': cost_no_battery,
            'raw_reward': raw_reward,
            'p2p_volume': p2p_vol,
            'grid_volume': grid_vol,
            'import_price': import_price,
            'export_price': export_price,
            'action': action,
            'action_power': action_power,
            'demand_delta': demand_delta,
        }
        
        return obs, reward, terminated, truncated, info
    
    def _get_observation(self):
        """Build the 11-dimensional state vector for the current timestep."""
        global_idx = self.current_episode_start + self.current_step
        
        # Clamp index to valid range (for terminal observation)
        global_idx = min(global_idx, len(self.df) - 1)
        
        obs = np.zeros(11, dtype=np.float32)
        obs[0] = self.raw_demands[global_idx]       # net_demand (1_Prosumer)
        obs[1] = self.battery.soc                     # battery SoC
        obs[2:11] = self.market_features[global_idx]  # 9 market features
        
        return obs
