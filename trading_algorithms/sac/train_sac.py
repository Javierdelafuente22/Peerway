"""
SAC Training Script for P2P Energy Trading.

Usage:
    python train_sac.py --timesteps 500000

Key differences from PPO:
    - Off-policy: replay buffer reuses each transition hundreds of times
    - Automatic entropy tuning (ent_coef='auto')
    - Adds rolling average price feature (12 dims instead of 11)
    - No VecNormalize needed (but still used for stability)

Reuses: rl_env/ (environment, battery, clearing), plot_training.py, utils/
"""

import argparse
import os
import numpy as np
import pandas as pd

from stable_baselines3 import SAC
from stable_baselines3.common.callbacks import BaseCallback
from stable_baselines3.common.monitor import Monitor
from stable_baselines3.common.vec_env import DummyVecEnv, VecNormalize

import gymnasium as gym
from gymnasium import spaces

from rl_env.battery import Battery
from rl_env.orderbook_clearing import clear_market_for_agent
from rl_env.p2p_energy_env import MAX_RATE, TARGET_AGENT, OTHER_AGENTS, MARKET_FEATURES
from utils.data_loader import load_and_split, print_split_info
from utils.evaluation import run_evaluation_pipeline
from plot_training import plot_lines, plot_shaded_both, plot_shaded_test_only


# ============================================================
# Feature engineering: add rolling price average to dataframe
# ============================================================
def add_rolling_price_feature(df, window=24):
    """
    Add a rolling mean of import_price over the last `window` hours.
    
    This gives the agent price context (is the current price high or low
    relative to recent history?) — the same information the heuristic uses
    via price percentiles.
    
    Uses min_periods=1 so early rows still get a value (shorter window).
    """
    df = df.copy()
    df['import_price_rolling_avg'] = (
        df['import_price']
        .rolling(window=window, min_periods=1)
        .mean()
        .astype(np.float32)
    )
    return df


# ============================================================
# Extended environment with rolling price feature (12 dims)
# ============================================================
EXTENDED_FEATURES = MARKET_FEATURES + ['import_price_rolling_avg']


class P2PEnergySACEnv(gym.Env):
    """
    Same as P2PEnergyTradingEnv but with 12 observation dims
    (adds rolling average of import price).
    """
    metadata = {"render_modes": []}

    def __init__(self, df, reward_scale=10.0, episode_length=24):
        super().__init__()
        self.df = df.reset_index(drop=True)
        self.reward_scale = reward_scale
        self.episode_length = episode_length

        # Precompute arrays
        self.raw_demands = self.df[TARGET_AGENT].values.astype(np.float32)
        self.market_features = self.df[EXTENDED_FEATURES].values.astype(np.float32)
        self.import_prices = self.df['import_price'].values.astype(np.float32)
        self.export_prices = self.df['export_price'].values.astype(np.float32)
        self.others_demands = self.df[OTHER_AGENTS].values.astype(np.float32)

        total_rows = len(self.df)
        self.episode_starts = list(range(0, total_rows - episode_length + 1, episode_length))
        if len(self.episode_starts) == 0:
            raise ValueError(f"Dataset too small ({total_rows} rows)")

        self.battery = Battery(capacity=1.0, max_rate=0.4, efficiency=0.95, initial_soc=0.0)

        # Continuous action [-1, 1]
        self.action_space = spaces.Box(low=-1.0, high=1.0, shape=(1,), dtype=np.float32)

        # 12 dims: demand, soc, 9 market features, rolling avg price
        self.observation_space = spaces.Box(
            low=-1.5, high=1.5, shape=(12,), dtype=np.float32
        )

        self.current_episode_start = 0
        self.current_step = 0
        self.episode_idx = 0

    def reset(self, seed=None, options=None):
        super().reset(seed=seed)
        self.current_episode_start = self.episode_starts[self.episode_idx % len(self.episode_starts)]
        self.episode_idx += 1
        self.current_step = 0
        self.battery.reset()
        return self._get_observation(), {}

    def step(self, action):
        global_idx = self.current_episode_start + self.current_step

        raw_demand = float(self.raw_demands[global_idx])
        import_price = float(self.import_prices[global_idx])
        export_price = float(self.export_prices[global_idx])
        others = self.others_demands[global_idx]

        # Continuous action
        action_scalar = float(np.clip(np.asarray(action).flatten()[0], -1.0, 1.0))
        action_power = action_scalar * MAX_RATE
        demand_delta, new_soc = self.battery.apply_action(action_power)
        modified_demand = raw_demand + demand_delta

        # Two clearings for reward (battery contribution only)
        cost_no_battery, _, _ = clear_market_for_agent(raw_demand, others, import_price, export_price)
        actual_cost, p2p_vol, grid_vol = clear_market_for_agent(modified_demand, others, import_price, export_price)

        raw_reward = cost_no_battery - actual_cost
        reward = float(raw_reward * self.reward_scale)

        # Time limit = truncated (not terminated)
        self.current_step += 1
        terminated = False
        truncated = self.current_step >= self.episode_length

        done = terminated or truncated
        if done:
            obs = np.zeros(12, dtype=np.float32)
            obs[0] = raw_demand
            obs[1] = new_soc
            obs[2:12] = self.market_features[global_idx]
        else:
            obs = self._get_observation()

        info = {
            'actual_cost': actual_cost,
            'cost_no_battery': cost_no_battery,
            'raw_reward': raw_reward,
            'action': action_scalar,
            'soc': new_soc,
        }
        return obs, reward, terminated, truncated, info

    def _get_observation(self):
        global_idx = self.current_episode_start + self.current_step
        global_idx = min(global_idx, len(self.df) - 1)
        obs = np.zeros(12, dtype=np.float32)
        obs[0] = self.raw_demands[global_idx]
        obs[1] = self.battery.soc
        obs[2:12] = self.market_features[global_idx]  # 10 market features (incl rolling avg)
        return obs


# ============================================================
# Callback (same structure as PPO)
# ============================================================
class RewardTrackingCallback(BaseCallback):
    def __init__(self, eval_env, eval_freq=10_000, n_eval_episodes=10,
                 episode_log_freq=1000, verbose=1):
        super().__init__(verbose)
        self.eval_env = eval_env
        self.eval_freq = eval_freq
        self.n_eval_episodes = n_eval_episodes
        self.episode_log_freq = episode_log_freq
        self.episode_log = [
            {'timestep': 0, 'episode': 0, 'reward': 0.0, 'source': 'train'},
            {'timestep': 0, 'episode': 0, 'reward': 0.0, 'source': 'eval'},
        ]
        self._total_train_episodes = 0
        self.best_reward = -np.inf

    def _on_step(self):
        infos = self.locals.get('infos', [])
        for info in infos:
            if 'episode' in info:
                self._total_train_episodes += 1
                ep_reward = float(info['episode']['r'])
                if self._total_train_episodes % self.episode_log_freq == 0:
                    self.episode_log.append({
                        'timestep': self.num_timesteps,
                        'episode': self._total_train_episodes,
                        'reward': ep_reward,
                        'source': 'train',
                    })

        if self.n_calls % self.eval_freq == 0:
            rewards = []
            for _ in range(self.n_eval_episodes):
                obs = self.eval_env.reset()
                done = False
                episode_reward = 0.0
                while not done:
                    action, _ = self.model.predict(obs, deterministic=True)
                    obs, reward, dones, info = self.eval_env.step(action)
                    raw_reward = self.eval_env.get_original_reward()[0]
                    episode_reward += float(raw_reward)
                    done = bool(dones[0])
                rewards.append(episode_reward)

            mean_eval_reward = float(np.mean(rewards))
            self.episode_log.append({
                'timestep': self.num_timesteps,
                'episode': self._total_train_episodes,
                'reward': mean_eval_reward,
                'source': 'eval',
            })

            if self.verbose:
                recent_train = [e['reward'] for e in self.episode_log if e['source'] == 'train'][-10:]
                mean_train = float(np.mean(recent_train)) if recent_train else np.nan
                print(f"  Step {self.num_timesteps:>7d} | Train: {mean_train:7.3f} | Eval: {mean_eval_reward:7.3f}")

            if mean_eval_reward > self.best_reward:
                self.best_reward = mean_eval_reward

        return True


# ============================================================
# Main
# ============================================================
def train(args):
    print("\n" + "=" * 55)
    print("SAC TRAINING — P2P Energy Trading")
    print("=" * 55)

    os.makedirs(args.output_dir, exist_ok=True)

    # Load and split
    df_train, df_test, split_info = load_and_split(args.data, train_ratio=0.8)
    print_split_info(split_info)

    # Add rolling price feature
    df_train = add_rolling_price_feature(df_train, window=24)
    df_test = add_rolling_price_feature(df_test, window=24)
    print("  Added feature: import_price_rolling_avg (24h window)")

    # Create environments
    def make_train_env():
        return Monitor(P2PEnergySACEnv(df_train, reward_scale=args.reward_scale))

    def make_eval_env():
        return P2PEnergySACEnv(df_test, reward_scale=args.reward_scale)

    train_env = DummyVecEnv([make_train_env])
    train_env = VecNormalize(train_env, norm_obs=True, norm_reward=True,
                             clip_obs=10.0, gamma=args.gamma)

    eval_env = DummyVecEnv([make_eval_env])
    eval_env = VecNormalize(eval_env, norm_obs=True, norm_reward=True,
                            clip_obs=10.0, gamma=args.gamma, training=False)

    print(f"  Train env: {split_info['train_days']} days")
    print(f"  Test env:  {split_info['test_days']} days")
    print(f"  Obs dims:  12 (11 original + rolling avg price)")
    print(f"  Action:    continuous [-1, 1]")

    # SAC model
    print(f"\nTraining SAC for {args.timesteps:,} timesteps...")
    print(f"  LR:           {args.lr}")
    print(f"  Buffer size:  {args.buffer_size:,}")
    print(f"  Batch size:   {args.batch_size}")
    print(f"  Entropy:      auto (SAC learns it)")
    print(f"  Network:      [{args.net_width}, {args.net_width}]")

    model = SAC(
        "MlpPolicy",
        train_env,
        learning_rate=args.lr,
        buffer_size=args.buffer_size,
        learning_starts=args.learning_starts,
        batch_size=args.batch_size,
        tau=0.005,              # Soft update coefficient for target network
        gamma=args.gamma,
        train_freq=4,           # Collect 4 steps before updating (faster than 1)
        gradient_steps=4,       # 4 gradient steps per update batch
        ent_coef='auto',        # SAC auto-tunes entropy (no manual tuning needed)
        target_update_interval=1,
        verbose=1,
        tensorboard_log=args.log_dir,
        seed=args.seed,
        device='cpu',
        policy_kwargs=dict(
            net_arch=[args.net_width, args.net_width],
        ),
    )

    # Sync normalisation stats
    eval_env.obs_rms = train_env.obs_rms
    eval_env.ret_rms = train_env.ret_rms

    callback = RewardTrackingCallback(
        eval_env=eval_env,
        eval_freq=args.eval_freq,
        n_eval_episodes=10,
        verbose=1,
    )

    try:
        model.learn(
            total_timesteps=args.timesteps,
            callback=callback,
            progress_bar=True,
        )
    except KeyboardInterrupt:
        print("\n\nTraining interrupted — saving progress...")

    # Save CSV + plots
    episode_df = pd.DataFrame(callback.episode_log)
    csv_path = os.path.join(args.output_dir, 'training_episodes.csv')
    episode_df.to_csv(csv_path, index=False)
    n_train = len(episode_df[episode_df['source'] == 'train'])
    n_eval = len(episode_df[episode_df['source'] == 'eval'])
    print(f"Episode log: {n_train} train + {n_eval} eval = {len(episode_df)} total")

    plot_lines(episode_df, os.path.join(args.output_dir, 'plot1_lines.png'))
    plot_shaded_both(episode_df, os.path.join(args.output_dir, 'plot2_shaded_both.png'))
    plot_shaded_test_only(episode_df, os.path.join(args.output_dir, 'plot3_shaded_test.png'))

    # Save model
    model_path = os.path.join(args.output_dir, "sac_p2p_trading")
    model.save(model_path)
    train_env.save(os.path.join(args.output_dir, "vec_normalize.pkl"))
    print(f"\nModel saved to: {model_path}.zip")

    # Final evaluation using orderbook_basic.py
    # Strategy: generate modified CSV via evaluation pipeline (which builds obs
    # using the 11-dim format), then clean the rolling avg column before
    # running orderbook_basic.py which doesn't expect it.
    print("\nFinal evaluation on TEST set...")

    obs_rms = train_env.obs_rms
    clip_obs = train_env.clip_obs
    epsilon = train_env.epsilon

    def normalize_obs(obs):
        return np.clip(
            (obs - obs_rms.mean) / np.sqrt(obs_rms.var + epsilon),
            -clip_obs, clip_obs
        ).astype(np.float32)

    test_rolling_avg = df_test['import_price_rolling_avg'].values.astype(np.float32)
    eval_step_counter = [0]

    def trained_policy(obs_11):
        """
        Evaluation pipeline passes 11-dim obs.
        We append the rolling avg price to make it 12-dim, normalise, predict.
        """
        idx = eval_step_counter[0]
        idx = min(idx, len(test_rolling_avg) - 1)

        obs_12 = np.zeros(12, dtype=np.float32)
        obs_12[0:11] = obs_11
        obs_12[11] = test_rolling_avg[idx]

        norm_obs = normalize_obs(obs_12)
        action, _ = model.predict(norm_obs, deterministic=True)
        eval_step_counter[0] += 1
        return float(np.asarray(action).flatten()[0])

    # Step 1: Generate modified CSV (with battery actions applied)
    from utils.evaluation import generate_modified_csv
    modified_csv = os.path.join(args.output_dir, 'orderbook_modified_sac.csv')
    generate_modified_csv(df_test, trained_policy, modified_csv, episode_length=24)

    # Step 2: Remove rolling avg column so orderbook_basic.py doesn't choke
    csv_df = pd.read_csv(modified_csv)
    if 'import_price_rolling_avg' in csv_df.columns:
        csv_df = csv_df.drop(columns=['import_price_rolling_avg'])
        csv_df.to_csv(modified_csv, index=False)

    # Step 3: Run orderbook clearing for exact KPIs
    from trading_algorithms.orderbook_basic import run_energy_market_simulation_no_battery
    run_energy_market_simulation_no_battery(
        input_file=modified_csv,
        alpha_file=args.alpha_file,
        detailed_transactions=os.path.join(args.output_dir, 'detailed_sac.csv'),
        summary_transactions=os.path.join(args.output_dir, 'summary_sac.csv'),
        target_agents=[TARGET_AGENT]
    )

    # Step 4: Clean up intermediate CSV
    if not args.keep_intermediate and os.path.exists(modified_csv):
        os.remove(modified_csv)

    print("\n" + "=" * 55)
    print("FILES SAVED in", args.output_dir)
    print("=" * 55)
    print("  summary_sac.csv            (SAC KPIs)")
    print("  detailed_sac.csv           (per-step transactions)")
    print("  training_episodes.csv      (episode reward data)")
    print("  plot1/2/3_*.png            (training curves)")
    print("  sac_p2p_trading.zip        (trained model)")
    print("  vec_normalize.pkl          (normalization stats)")
    print("=" * 55)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train SAC for P2P Energy Trading")
    parser.add_argument("--data", type=str, default="data/orderbook.csv")
    parser.add_argument("--alpha_file", type=str, default="data/alphas.csv")
    parser.add_argument("--timesteps", type=int, default=500_000)
    parser.add_argument("--lr", type=float, default=3e-4)
    parser.add_argument("--buffer_size", type=int, default=100_000,
                        help="Replay buffer size")
    parser.add_argument("--learning_starts", type=int, default=2400,
                        help="Random actions before learning starts (100 episodes)")
    parser.add_argument("--batch_size", type=int, default=256)
    parser.add_argument("--gamma", type=float, default=0.99)
    parser.add_argument("--net_width", type=int, default=128,
                        help="Width of each hidden layer [N, N]")
    parser.add_argument("--reward_scale", type=float, default=10.0)
    parser.add_argument("--eval_freq", type=int, default=10_000)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--output_dir", type=str, default="orderbook_results/sac")
    parser.add_argument("--log_dir", type=str, default="logs/tensorboard_sac")
    parser.add_argument("--keep_intermediate", action="store_true")

    args = parser.parse_args()
    train(args)
