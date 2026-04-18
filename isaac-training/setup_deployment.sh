#!/usr/bin/env bash
set -euo pipefail

ENV_NAME="${NAV_ENV_NAME:-NavRL}"
TORCH_VERSION="${TORCH_VERSION:-2.1.0}"
VISION_VERSION="${VISION_VERSION:-0.16.0}"
AUDIO_VERSION="${AUDIO_VERSION:-2.1.0}"
TORCHRL_VERSION="${TORCHRL_VERSION:-0.2.1}"
TENSORDICT_VERSION="${TENSORDICT_VERSION:-0.2.1}"

if ! command -v conda >/dev/null 2>&1; then
    echo "conda 未找到，请先安装 Miniconda/Anaconda。"
    exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

eval "$(conda shell.bash hook)"

echo "[1/3] Creating conda env..."
conda create -y -n "$ENV_NAME" python=3.10 -c conda-forge
conda activate "$ENV_NAME"
pip install --upgrade pip
pip install "torch==${TORCH_VERSION}" "torchvision==${VISION_VERSION}" "torchaudio==${AUDIO_VERSION}"
pip install numpy==1.26.4
pip install "pydantic!=1.7,!=1.7.1,!=1.7.2,!=1.7.3,!=1.8,!=1.8.1,<2.0.0,>=1.6.2"
pip install hydra-core omegaconf einops pyyaml rospkg matplotlib pandas plotly
pip install wandb==0.12.21 imageio imageio-ffmpeg==0.4.9 moviepy==1.0.3 av setproctitle

echo "[2/3] Installing OmniDrones package..."
cd "$SCRIPT_DIR/third_party/OmniDrones"
pip install -e .

echo "[3/3] Installing TorchRL/TensorDict..."
pip install --no-deps "tensordict==${TENSORDICT_VERSION}" "torchrl==${TORCHRL_VERSION}"

python -c "import torch; print(torch.__version__)"
echo "Deployment setup completed. Activate environment with: conda activate ${ENV_NAME}"
