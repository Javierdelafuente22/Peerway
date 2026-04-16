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
import matplotlib.pyplot as plt

from stable_baselines3 import PPO
from stable_baselines3.common.callbacks import BaseCallback
from stable_baselines3.common.monitor import Monitor
from stable_baselines3.common.vec_env import DummyVecEnv, VecNormalize

from rl_env.p2p_energy_env import P2PEnergyTradingEnv, ACTION_MAP
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
    Periodically evaluates the policy on the test env and records mean reward.
    Also tracks training reward (from Monitor-wrapped train env).
    
    IMPORTANT: The eval env must have the SAME VecNormalize stats as the train env,
    otherwise the policy sees differently-scaled inputs. We handle this by passing
    a normalized eval env that shares stats with the training env.
    """
    
    def __init__(self, eval_env, eval_freq=10_000, n_eval_episodes=10, verbose=1):
        super().__init__(verbose)
        self.eval_env = eval_env
        self.eval_freq = eval_freq
        self.n_eval_episodes = n_eval_episodes
        self.timesteps = []
        self.eval_rewards = []
        self.train_rewards = []
        self.best_reward = -np.inf
        
    def _on_step(self):
        if self.n_calls % self.eval_freq == 0:
            # Test set evaluation (deterministic policy)
            # IMPORTANT: eval_env is VecNormalize-wrapped with norm_reward=True.
            # We use get_original_reward() to get the raw (unnormalised) reward,
            # so it's on the same scale as the training reward from ep_info_buffer.
            rewards = []
            for _ in range(self.n_eval_episodes):
                obs = self.eval_env.reset()
                done = False
                episode_reward = 0.0
                while not done:
                    action, _ = self.model.predict(obs, deterministic=True)
                    obs, reward, dones, info = self.eval_env.step(action)
                    # Use unnormalised reward for consistent comparison with training
                    raw_reward = self.eval_env.get_original_reward()[0]
                    episode_reward += float(raw_reward)
                    done = bool(dones[0])
                rewards.append(episode_reward)
            
            mean_eval_reward = float(np.mean(rewards))
            
            # Training reward from Monitor's rolling buffer
            ep_info = self.model.ep_info_buffer
            if ep_info is not None and len(ep_info) > 0:
                mean_train_reward = float(np.mean([ep['r'] for ep in ep_info]))
            else:
                mean_train_reward = np.nan
            
            self.timesteps.append(self.n_calls)
            self.eval_rewards.append(mean_eval_reward)
            self.train_rewards.append(mean_train_reward)
            
            if self.verbose:
                print(f"  Step {self.n_calls:>7d} | Train: {mean_train_reward:7.3f} | Eval: {mean_eval_reward:7.3f}")
            
            self.logger.record("eval/mean_reward", mean_eval_reward)
            self.logger.record("train/mean_reward", mean_train_reward)
            
            if mean_eval_reward > self.best_reward:
                self.best_reward = mean_eval_reward
        
        return True


def plot_reward_curve(callback, output_path):
    """Save training + eval reward curves on same plot."""
    if len(callback.timesteps) == 0:
        print("No reward data to plot.")
        return
    
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.plot(callback.timesteps, callback.train_rewards, marker='s', linewidth=2,
            color='#f97316', label='Training', alpha=0.8)
    ax.plot(callback.timesteps, callback.eval_rewards, marker='o', linewidth=2,
            color='#2563eb', label='Test (unseen data)')
    ax.axhline(y=callback.best_reward, color='#16a34a', linestyle='--', alpha=0.5,
               label=f'Best eval: {callback.best_reward:.2f}')
    ax.set_xlabel('Training Timesteps')
    ax.set_ylabel('Mean Episode Reward')
    ax.set_title('PPO Training: Train vs Test Reward Curves')
    ax.grid(True, alpha=0.3)
    ax.legend(loc='lower right')
    plt.tight_layout()
    plt.savefig(output_path, dpi=120)
    plt.close()
    print(f"Reward plot saved to: {output_path}")


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
    print(f"  Action space size: {len(ACTION_MAP)} (actions: {list(ACTION_MAP.values())})")
    print(f"  VecNormalize: observations normalised with running mean/std")
    
    # ---------- [3/4] Train PPO ----------
    print(f"\n[3/4] Training PPO for {args.timesteps:,} timesteps...")
    print(f"  Learning rate:  LINEAR schedule {args.lr} -> 0")
    print(f"  Entropy coef:   {args.ent_coef}")
    print(f"  Gamma:          {args.gamma}")
    
    model = PPO(
        "MlpPolicy",
        train_env,
        learning_rate=linear_schedule(args.lr),  # Linear decay
        n_steps=2048,
        batch_size=64,
        n_epochs=10,
        gamma=args.gamma,
        gae_lambda=0.95,
        clip_range=0.2,
        ent_coef=args.ent_coef,
        verbose=1,  # Print training stats: explained_variance, KL, clip_fraction, entropy
        tensorboard_log=args.log_dir,
        seed=args.seed,
        device='cpu',
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
    
    model.learn(
        total_timesteps=args.timesteps,
        callback=reward_callback,
        progress_bar=True,
    )
    
    # Save reward curves
    plot_path = os.path.join(args.output_dir, 'training_reward_curve.png')
    plot_reward_curve(reward_callback, plot_path)
    
    reward_df = pd.DataFrame({
        'timesteps': reward_callback.timesteps,
        'train_reward': reward_callback.train_rewards,
        'eval_reward': reward_callback.eval_rewards,
    })
    reward_df.to_csv(os.path.join(args.output_dir, 'training_reward_curve.csv'), index=False)
    
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
        return int(action)
    
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
    print("  training_reward_curve.png  (train + eval curves)")
    print("  training_reward_curve.csv  (raw reward data)")
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
    parser.add_argument("--timesteps", type=int, default=1_000_000,
                        help="Total training timesteps (Tier 1 default: 1M)")
    parser.add_argument("--lr", type=float, default=3e-4,
                        help="Initial learning rate (decays linearly to 0)")
    parser.add_argument("--reward_scale", type=float, default=10.0)
    parser.add_argument("--ent_coef", type=float, default=0.01,
                        help="Entropy bonus (higher = more exploration)")
    parser.add_argument("--gamma", type=float, default=0.99,
                        help="Discount factor")
    parser.add_argument("--eval_freq", type=int, default=10_000)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--output_dir", type=str, default="orderbook_results")
    parser.add_argument("--log_dir", type=str, default="logs/tensorboard")
    parser.add_argument("--keep_intermediate", action="store_true")
    
    args = parser.parse_args()
    train(args)
