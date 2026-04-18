#!/usr/bin/env bash
set -euo pipefail

ENV_NAME="${NAV_ENV_NAME:-aml_safe_nav}"
TORCHRL_VERSION="${TORCHRL_VERSION:-0.2.1}"
TENSORDICT_VERSION="${TENSORDICT_VERSION:-0.2.1}"

if ! command -v conda >/dev/null 2>&1; then
    echo "conda 未找到，请先安装 Miniconda/Anaconda。"
    exit 1
fi

if [ -z "${ISAACSIM_PATH:-}" ]; then
    echo "请先设置 ISAACSIM_PATH，例如："
    echo "export ISAACSIM_PATH=/absolute/path/to/isaac-sim-2023.1.0-hotfix.1"
    exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

eval "$(conda shell.bash hook)"
conda create -y -n "$ENV_NAME" python=3.10

echo "[1/5] Setting up Orbit..."
cd "$SCRIPT_DIR/third_party/orbit"

if [ -L "_isaac_sim" ]; then
    rm -rf _isaac_sim
elif [ -e "_isaac_sim" ]; then
    echo "_isaac_sim 已存在但不是软链接，请手动删除后重试。"
    exit 1
fi

ln -s "${ISAACSIM_PATH}" _isaac_sim
./orbit.sh --conda "$ENV_NAME"

conda activate "$ENV_NAME"
pip install --upgrade pip
pip install numpy==1.26.4
pip install "pydantic!=1.7,!=1.7.1,!=1.7.2,!=1.7.3,!=1.8,!=1.8.1,<2.0.0,>=1.6.2"
pip install hydra-core omegaconf einops pyyaml rospkg matplotlib pandas plotly
pip install wandb==0.12.21 imageio imageio-ffmpeg==0.4.9 moviepy==1.0.3 av setproctitle

echo "[2/5] Installing system dependencies..."
sudo apt update && sudo apt install -y cmake build-essential

echo "[3/5] Installing Orbit dependencies..."
./orbit.sh --install

echo "[4/5] Installing OmniDrones..."
cd "$SCRIPT_DIR/third_party/OmniDrones"
cp -r conda_setup/etc "$CONDA_PREFIX"
conda activate "$ENV_NAME"
python -c "from omni.isaac.kit import SimulationApp"
pip install -e .

echo "[5/5] Installing TorchRL/TensorDict..."
# 原始压缩包缺失 third_party/tensordict 与 third_party/rl，因此这里改为安装公开 wheel。
pip install --no-deps "tensordict==${TENSORDICT_VERSION}" "torchrl==${TORCHRL_VERSION}"

python -c "import torch; print(torch.__version__)"
echo "Setup completed successfully. Activate environment with: conda activate ${ENV_NAME}"
