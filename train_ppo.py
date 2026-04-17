"""
PPO Training Script for P2P Energy Trading.

Usage:
    python train_ppo.py --data data/orderbook.csv --timesteps 1000000

TIER 1 IMPROVEMENTS (vs initial version):
    1. VecNormalize wrapper: running mean/std normalization of observations.
       Recommended by SB3 docs for all custom environments. Stabilises training.
    2. Linear learning rate schedule: LR decays from initial value to 0 over training.
       Prevents late-training policy collapse after finding a good strategy.
    3. Default timesteps increased to 1M: RL needs more data than supervised learning.
       500K was short for this problem.

Pipeline:
    [1/4] Load data, create train/test split
    [2/4] Create environments (with VecNormalize)
    [3/4] Train PPO with linear LR schedule
    [4/4] Evaluate on test set using orderbook_basic.py for exact KPIs
"""

import argparse
import os
from typing import Callable

import numpy as np
import pandas as pd

from stable_baselines3 import PPO
from stable_baselines3.common.callbacks import BaseCallback
from stable_baselines3.common.monitor import Monitor
from stable_baselines3.common.vec_env import DummyVecEnv, VecNormalize

from rl_env.p2p_energy_env import P2PEnergyTradingEnv, MAX_RATE
from utils.data_loader import load_and_split, print_split_info
from utils.evaluation import run_evaluation_pipeline


# ============================================================
# Linear learning rate schedule
# ============================================================
def linear_schedule(initial_value: float) -> Callable[[float], float]:
    """
    Linear learning rate schedule.
    Starts at `initial_value`, decays linearly to 0 as training progresses.
    
    SB3 calls the schedule with `progress_remaining` (1.0 at start, 0.0 at end).
    """
    def func(progress_remaining: float) -> float:
        return progress_remaining * initial_value
    return func


# ============================================================
# Callback: tracks both training and eval reward over time
# ============================================================
class RewardTrackingCallback(BaseCallback):
    """
    Tracks training and eval episode rewards for plotting.
    
    - Training: logs every Nth completed episode's reward.
    - Eval: logs the MEAN of eval episodes at each checkpoint (one point per checkpoint).
    - Inserts a (0, 0) starting point so plots begin at zero.
    """
    
    def __init__(self, eval_env, eval_freq=10_000, n_eval_episodes=10,
                 episode_log_freq=1000, verbose=1):
        super().__init__(verbose)
        self.eval_env = eval_env
        self.eval_freq = eval_freq
        self.n_eval_episodes = n_eval_episodes
        self.episode_log_freq = episode_log_freq
        self.episode_log = []
        self._total_train_episodes = 0
        self.best_reward = -np.inf
        # Insert starting point at zero so plots begin from origin
        self.episode_log.append({
            'timestep': 0, 'episode': 0, 'reward': 0.0, 'source': 'train',
        })
        self.episode_log.append({
            'timestep': 0, 'episode': 0, 'reward': 0.0, 'source': 'eval',
        })
        
    def _on_step(self):
        # --- Detect training episode completion via Monitor wrapper ---
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
        
        # --- Periodic eval on test set ---
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
            
            # Log ONE point per eval checkpoint: the mean reward
            mean_eval_reward = float(np.mean(rewards))
            self.episode_log.append({
                'timestep': self.num_timesteps,
                'episode': self._total_train_episodes,
                'reward': mean_eval_reward,
                'source': 'eval',
            })
            
            if self.verbose:
                recent_train = [e['reward'] for e in self.episode_log
                                if e['source'] == 'train'][-10:]
                mean_train = float(np.mean(recent_train)) if recent_train else np.nan
                print(f"  Step {self.num_timesteps:>7d} | Train: {mean_train:7.3f} | Eval: {mean_eval_reward:7.3f}")
            
            self.logger.record("eval/mean_reward", mean_eval_reward)
            
            if mean_eval_reward > self.best_reward:
                self.best_reward = mean_eval_reward
        
        return True


# ============================================================
# Main training function
# ============================================================
def train(args):
    print("\n" + "=" * 55)
    print("P2P ENERGY TRADING - PPO TRAINING (Tier 1 tuned)")
    print("=" * 55)
    
    os.makedirs(args.output_dir, exist_ok=True)
    
    # ---------- [1/4] Load data ----------
    print("\n[1/4] Loading data...")
    df_train, df_test, split_info = load_and_split(args.data, train_ratio=0.8)
    print_split_info(split_info)
    
    # ---------- [2/4] Create environments ----------
    print("\n[2/4] Creating environments...")
    
    # Training env: wrapped in Monitor (tracks episode rewards) and VecNormalize
    def make_train_env():
        return Monitor(P2PEnergyTradingEnv(df_train, reward_scale=args.reward_scale))
    
    train_env = DummyVecEnv([make_train_env])
    # VecNormalize: computes running mean/std of obs AND rewards
    # norm_reward=True: helps when reward signal is noisy relative to its scale
    #   (research recommendation for noisy reward signals)
    # clip_obs=10.0: normalised obs are clipped to [-10, 10]
    train_env = VecNormalize(
        train_env,
        norm_obs=True,
        norm_reward=True,
        clip_obs=10.0,
        gamma=args.gamma,
    )
    
    # Eval env: SAME VecNormalize stats as train env (critical!)
    # We wrap a DummyVecEnv around test data, then load train's stats into it.
    def make_eval_env():
        return P2PEnergyTradingEnv(df_test, reward_scale=args.reward_scale)
    
    eval_env = DummyVecEnv([make_eval_env])
    eval_env = VecNormalize(
        eval_env,
        norm_obs=True,
        norm_reward=True,
        clip_obs=10.0,
        gamma=args.gamma,
        training=False,  # Don't update stats; use train env's stats
    )
    # Share observation stats with train env (set after training starts)
    # We'll sync this inside the callback workflow
    
    print(f"  Train env: {split_info['train_days']} episodes (days)")
    print(f"  Test env:  {split_info['test_days']} episodes (days)")
    print(f"  Action space: continuous [-1, 1], scaled to battery power [-{MAX_RATE}, {MAX_RATE}]")
    print(f"  VecNormalize: observations normalised with running mean/std")
    
    # ---------- [3/4] Train PPO ----------
    print(f"\n[3/4] Training PPO for {args.timesteps:,} timesteps...")
    print(f"  Learning rate:  CONSTANT {args.lr} (no decay)")
    print(f"  Entropy coef:   {args.ent_coef}")
    print(f"  Gamma:          {args.gamma}")
    print(f"  Network arch:   [256, 256]")
    print(f"  Initial log_std: {args.log_std_init} (std = {np.exp(args.log_std_init):.3f})")
    
    model = PPO(
        "MlpPolicy",
        train_env,
        # Constant LR (no linear decay). Prior run decayed to 1e-7 and froze the
        # policy before it could learn; constant LR keeps updates meaningful throughout.
        learning_rate=args.lr,
        n_steps=2048,
        # batch_size=256 (was 64) -> 8 minibatches per update instead of 32.
        # Fewer gradient steps per rollout reduces overfitting to each batch of data.
        batch_size=256,
        n_epochs=10,
        gamma=args.gamma,
        gae_lambda=0.95,
        clip_range=0.2,
        # Higher entropy coef (was 0.01) keeps the policy exploring longer.
        # Prior run's policy collapsed to near-deterministic too fast.
        ent_coef=args.ent_coef,
        max_grad_norm=0.5,  # Explicit (SB3 default). Prevents large gradient spikes.
        verbose=1,
        tensorboard_log=args.log_dir,
        seed=args.seed,
        device='cpu',
        policy_kwargs=dict(
            # log_std_init=0 means initial action noise std = exp(0) = 1.0.
            # (Was -1.0 -> std ~0.37). More aggressive exploration at start.
            log_std_init=args.log_std_init,
            # Bigger network: [256, 256] instead of default [64, 64].
            # More capacity to represent complex charge/discharge policies.
            net_arch=dict(pi=[256, 256], vf=[256, 256]),
        ),
    )
    
    # Sync eval env's normalization stats with train env's
    # (VecNormalize stats are updated during training; eval env mirrors them)
    eval_env.obs_rms = train_env.obs_rms
    eval_env.ret_rms = train_env.ret_rms
    
    reward_callback = RewardTrackingCallback(
        eval_env=eval_env,
        eval_freq=args.eval_freq,
        n_eval_episodes=10,
        verbose=1,
    )
    
    try:
        model.learn(
            total_timesteps=args.timesteps,
            callback=reward_callback,
            progress_bar=True,
        )
    except KeyboardInterrupt:
        print("\n\nTraining interrupted — saving progress so far...")
    
    # Save single CSV with all episode data (train + eval)
    episode_df = pd.DataFrame(reward_callback.episode_log)
    csv_path = os.path.join(args.output_dir, 'training_episodes.csv')
    episode_df.to_csv(csv_path, index=False)
    n_train = len(episode_df[episode_df['source'] == 'train'])
    n_eval = len(episode_df[episode_df['source'] == 'eval'])
    print(f"Episode log saved: {n_train} train + {n_eval} eval = {len(episode_df)} total")
    
    # Generate plots from the CSV (uses plot_training.py)
    from plot_training import plot_lines, plot_shaded_both, plot_shaded_test_only
    plot_lines(episode_df, os.path.join(args.output_dir, 'plot1_lines.png'))
    plot_shaded_both(episode_df, os.path.join(args.output_dir, 'plot2_shaded_both.png'))
    plot_shaded_test_only(episode_df, os.path.join(args.output_dir, 'plot3_shaded_test.png'))
    
    # Save model + VecNormalize stats (needed for deployment/re-evaluation)
    model_path = os.path.join(args.output_dir, "ppo_p2p_trading")
    model.save(model_path)
    vec_normalize_path = os.path.join(args.output_dir, "vec_normalize.pkl")
    train_env.save(vec_normalize_path)
    print(f"\nModel saved to:         {model_path}.zip")
    print(f"VecNormalize stats to:  {vec_normalize_path}")
    
    # ---------- [4/4] Final evaluation ----------
    # Build a policy that uses the trained model + VecNormalize stats.
    # The evaluation pipeline feeds raw obs; we must normalize them the same way.
    print("\n[4/4] Final evaluation on TEST set...")
    
    obs_rms = train_env.obs_rms  # running mean/std of observations
    clip_obs = train_env.clip_obs
    epsilon = train_env.epsilon
    
    def normalize_obs(obs):
        """Apply the same normalization used during training."""
        return np.clip(
            (obs - obs_rms.mean) / np.sqrt(obs_rms.var + epsilon),
            -clip_obs, clip_obs
        ).astype(np.float32)
    
    def trained_policy(obs):
        norm_obs = normalize_obs(obs)
        action, _ = model.predict(norm_obs, deterministic=True)
        # Continuous action is a 1D array; return as scalar
        return float(np.asarray(action).flatten()[0])
    
    run_evaluation_pipeline(
        df_test, trained_policy,
        output_dir=args.output_dir,
        policy_name="ppo",
        alpha_file=args.alpha_file,
        keep_intermediate=args.keep_intermediate,
    )
    
    print("\n" + "=" * 55)
    print("FILES SAVED in", args.output_dir)
    print("=" * 55)
    print("  summary_ppo.csv            (PPO KPIs)")
    print("  detailed_ppo.csv           (per-step transactions)")
    print("  training_episodes.csv      (per-episode reward data)")
    print("  plot1_lines.png            (train + test lines)")
    print("  plot2_shaded_both.png      (shaded range, train + test)")
    print("  plot3_shaded_test.png      (shaded range, test only)")
    print("  ppo_p2p_trading.zip        (trained model)")
    print("  vec_normalize.pkl          (normalization stats)")
    print("=" * 55)


# ============================================================
# CLI
# ============================================================
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train PPO for P2P Energy Trading")
    parser.add_argument("--data", type=str, default="data/orderbook.csv")
    parser.add_argument("--alpha_file", type=str, default="data/alphas.csv")
    parser.add_argument("--timesteps", type=int, default=500_000,
                        help="Total training timesteps (Tier 1 default: 1M)")
    parser.add_argument("--lr", type=float, default=3e-4,
                        help="Constant learning rate (no decay)")
    parser.add_argument("--reward_scale", type=float, default=10.0)
    parser.add_argument("--ent_coef", type=float, default=0.05,
                        help="Entropy bonus (higher = more exploration; was 0.01, now 0.05)")
    parser.add_argument("--log_std_init", type=float, default=-1.0,
                        help="Initial log-std for action noise (-1.0 -> std~0.37, moderate exploration)")
    parser.add_argument("--gamma", type=float, default=0.99,
                        help="Discount factor")
    parser.add_argument("--eval_freq", type=int, default=10_000)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--output_dir", type=str, default="orderbook_results/ppo")
    parser.add_argument("--log_dir", type=str, default="logs/tensorboard")
    parser.add_argument("--keep_intermediate", action="store_true")
    
    args = parser.parse_args()
    train(args)
