#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR/isaac-training/third_party/OmniDrones/scripts"

python train.py \
  task=SafeUAVNav \
  algo=ppo \
  headless="${HEADLESS:-false}" \
  total_frames="${TOTAL_FRAMES:-2000000}" \
  eval_interval="${EVAL_INTERVAL:-20}" \
  save_interval="${SAVE_INTERVAL:-20}" \
  wandb.mode="${WANDB_MODE:-disabled}" \
  env.num_envs="${NUM_ENVS:-256}" \
  "$@"
