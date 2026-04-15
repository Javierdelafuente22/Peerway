"""
PPO Training Script for P2P Energy Trading.

Usage:
    python train_ppo.py --data data/orderbook.csv --timesteps 500000

This script:
    1. Loads data and creates train/test split
    2. Creates the Gymnasium environment
    3. Trains PPO using Stable Baselines 3
    4. Evaluates on test set using orderbook_basic.py for exact KPIs
    5. Saves the trained model
"""

import argparse
import os
import numpy as np
import pandas as pd
from pathlib import Path

from stable_baselines3 import PPO
from stable_baselines3.common.callbacks import BaseCallback
from stable_baselines3.common.monitor import Monitor

from rl_env.p2p_energy_env import P2PEnergyTradingEnv, ACTION_MAP
from utils.data_loader import load_and_split, print_split_info
from utils.evaluation import run_evaluation_pipeline, no_battery_policy


# ============================================================
# Custom callback: logs episode metrics during training
# ============================================================
class TrainingMetricsCallback(BaseCallback):
    """Logs episode reward statistics during training."""
    
    def __init__(self, eval_env, eval_freq=5000, verbose=1):
        super().__init__(verbose)
        self.eval_env = eval_env
        self.eval_freq = eval_freq
        self.best_reward = -np.inf
        
    def _on_step(self):
        if self.n_calls % self.eval_freq == 0:
            rewards = []
            
            for _ in range(10):  # 10 episodes
                done = False
                obs, _ = self.eval_env.reset()
                episode_reward = 0
                while not done:
                    action, _ = self.model.predict(obs, deterministic=True)
                    obs, reward, terminated, truncated, info = self.eval_env.step(int(action))
                    episode_reward += reward
                    done = terminated or truncated
                rewards.append(episode_reward)
            
            mean_reward = np.mean(rewards)
            
            if self.verbose:
                print(f"  Step {self.n_calls:>7d} | Mean eval reward: {mean_reward:.3f}")
            
            self.logger.record("eval/mean_reward", mean_reward)
            
            if mean_reward > self.best_reward:
                self.best_reward = mean_reward
        
        return True


# ============================================================
# Main training function
# ============================================================
def train(args):
    """Run the full training pipeline."""
    
    print("\n" + "=" * 55)
    print("P2P ENERGY TRADING - PPO TRAINING")
    print("=" * 55)
    
    # 1. Load and split data
    print("\n[1/5] Loading data...")
    df_train, df_test, split_info = load_and_split(args.data, train_ratio=0.8)
    print_split_info(split_info)
    
    # 2. Create environments
    print("\n[2/5] Creating environments...")
    train_env = Monitor(P2PEnergyTradingEnv(df_train, reward_scale=args.reward_scale))
    eval_env = P2PEnergyTradingEnv(df_test, reward_scale=args.reward_scale)
    
    print(f"  Train env: {split_info['train_days']} episodes (days)")
    print(f"  Test env:  {split_info['test_days']} episodes (days)")
    
    # 3. Baseline evaluation (no battery, using exact orderbook logic)
    print("\n[3/5] Computing baseline on TEST set...")
    print("\n--- No Battery Baseline ---")
    run_evaluation_pipeline(
        df_test, no_battery_policy,
        output_dir=args.output_dir,
        policy_name="no_battery",
        alpha_file=args.alpha_file,
    )
    
    # 4. Train PPO
    print(f"\n[4/5] Training PPO for {args.timesteps:,} timesteps...")
    
    model = PPO(
        "MlpPolicy",
        train_env,
        learning_rate=args.lr,
        n_steps=2048,
        batch_size=64,
        n_epochs=10,
        gamma=0.99,
        gae_lambda=0.95,
        clip_range=0.2,
        ent_coef=0.01,
        verbose=0,
        tensorboard_log=args.log_dir,
        seed=args.seed,
        device='cpu',
    )
    
    metrics_callback = TrainingMetricsCallback(
        eval_env=eval_env,
        eval_freq=args.eval_freq,
        verbose=1
    )
    
    model.learn(
        total_timesteps=args.timesteps,
        callback=metrics_callback,
        progress_bar=True,
    )
    
    # 5. Final evaluation on test set (using exact orderbook logic)
    print("\n[5/5] Final evaluation on TEST set...")
    
    def trained_policy(obs):
        action, _ = model.predict(obs, deterministic=True)
        return int(action)
    
    print("\n--- Trained PPO Agent ---")
    run_evaluation_pipeline(
        df_test, trained_policy,
        output_dir=args.output_dir,
        policy_name="ppo",
        alpha_file=args.alpha_file,
    )
    
    # Save model
    model_path = os.path.join(args.output_dir, "ppo_p2p_trading")
    model.save(model_path)
    print(f"\nModel saved to: {model_path}")


# ============================================================
# CLI
# ============================================================
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train PPO for P2P Energy Trading")
    parser.add_argument("--data", type=str, default="data/orderbook.csv",
                        help="Path to orderbook CSV")
    parser.add_argument("--alpha_file", type=str, default="data/alphas.csv",
                        help="Path to alphas CSV")
    parser.add_argument("--timesteps", type=int, default=500_000,
                        help="Total training timesteps")
    parser.add_argument("--lr", type=float, default=3e-4,
                        help="Learning rate")
    parser.add_argument("--reward_scale", type=float, default=10.0,
                        help="Reward scaling factor")
    parser.add_argument("--eval_freq", type=int, default=10_000,
                        help="Evaluate every N steps")
    parser.add_argument("--seed", type=int, default=42,
                        help="Random seed")
    parser.add_argument("--output_dir", type=str, default="orderbook_results",
                        help="Directory for saved models and results")
    parser.add_argument("--log_dir", type=str, default="logs/tensorboard",
                        help="Tensorboard log directory")
    
    args = parser.parse_args()
    train(args)
