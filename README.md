# 基于强化学习与安全屏蔽的无人机动态环境自主导航方法研究

本仓库为《高级机器学习理论》课程作业代码提交仓库，研究主题为“基于强化学习与安全屏蔽的无人机动态环境自主导航方法研究”。

当前提交版只保留了 `ROS1` 相关部署代码，并整理出两个直接可用的入口：

1. `quick-demos/`：基于预训练策略的简单演示
2. `isaac-training/`：基于 Isaac Sim 的强化学习训练代码

同时保留 `ros1/` 作为完整的 ROS1/Gazebo 仿真部署版本，便于课程展示时运行完整导航流程。

![简单演示](media/simple-navigation.gif)

## 仓库结构说明

```text
.
├─ isaac-training/   # Isaac Sim 训练环境、任务配置和安装脚本
├─ quick-demos/      # 简单演示脚本、推理代码和预训练 checkpoint
├─ ros1/             # ROS1/Gazebo 仿真部署代码
├─ media/            # 仓库内保留的简单演示 GIF
├─ LICENSE
└─ README.md
```

如果你看到文件比较多，主要原因在于 `ros1/` 本身是一个完整的 ROS 工程，里面按功能拆成了多个 package：

- `ros1/uav_simulator/`：Gazebo 场景、模型、世界文件和无人机仿真
- `ros1/navigation_runner/`：导航策略、安全屏蔽和运行入口
- `ros1/map_manager/`：地图与碰撞查询模块
- `ros1/onboard_detector/`：动态障碍感知相关模块

这些目录都和最终的仿真运行直接相关，不是无关文件。

## 一、简单演示怎么运行

简单演示使用 `quick-demos/` 下的预训练模型，不依赖 ROS，适合作为课程作业展示时的快速运行入口。

### 环境建议

- Ubuntu 20.04/22.04
- Conda / Miniconda
- Python 3.10

### 1. 创建部署环境

```bash
cd isaac-training
bash setup_deployment.sh
conda activate NavRL
```

### 2. 运行简单演示

```bash
cd ../quick-demos
python simple-navigation.py
```

运行后会弹出可视化窗口，展示无人机在障碍环境中的目标点导航过程。

### 3. 如果需要导出 GIF

```bash
cd ../quick-demos
python simple-navigation.py --save-gif ../media/simple-navigation-local.gif --no-show
```

其中：

- `--save-gif` 用于保存演示结果
- `--no-show` 用于无界面导出

预训练模型位于：

```text
quick-demos/ckpts/navrl_checkpoint.pt
```

## 二、训练代码怎么运行

训练部分位于 `isaac-training/`，用于在 Isaac Sim 中训练强化学习导航策略。

### 环境要求

- Ubuntu 22.04
- NVIDIA GPU
- Conda / Miniconda
- Isaac Sim `2023.1.0-hotfix.1`

### 1. 设置 Isaac Sim 路径

```bash
export ISAACSIM_PATH=/absolute/path/to/isaac-sim-2023.1.0-hotfix.1
```

### 2. 安装训练环境

```bash
cd isaac-training
bash setup.sh
conda activate NavRL
```

### 3. 启动训练

```bash
cd third_party/OmniDrones/scripts
python train.py task=SafeUAVNav algo=ppo wandb.mode=disabled env.num_envs=256
```

如果希望无界面训练：

```bash
python train.py task=SafeUAVNav algo=ppo headless=True wandb.mode=disabled env.num_envs=256
```

训练任务配置位于：

```text
isaac-training/third_party/OmniDrones/cfg/task/SafeUAVNav.yaml
```

## 三、ROS1 仿真版本怎么运行

本仓库只保留 `ROS1` 版本，不包含 `ROS2` 代码。

### 环境要求

- Ubuntu 20.04
- ROS Noetic
- Gazebo

### 1. 安装依赖并编译 catkin 工作空间

```bash
sudo apt-get install ros-noetic-mavros*

cp -r ros1 /path/to/catkin_ws/src
cd /path/to/catkin_ws
catkin_make
```

### 2. 配置 Gazebo 模型路径

将下面这行加入 `~/.bashrc`：

```bash
source /path/to/catkin_ws/src/ros1/uav_simulator/gazeboSetup.bash
```

然后执行：

```bash
source ~/.bashrc
```

### 3. 启动仿真与导航

终端 1：

```bash
roslaunch uav_simulator start.launch
```

终端 2：

```bash
roslaunch navigation_runner safety_and_perception_sim.launch
```

终端 3：

```bash
conda activate NavRL
rosrun navigation_runner navigation_node.py
```

运行后可以在 RViz 中使用 `2D Nav Goal` 指定目标点，观察无人机在动态环境中的导航过程。

## 四、课程作业对应关系

这份代码提交对应的核心方法可以概括为：

1. 强化学习策略负责输出名义导航动作
2. 安全屏蔽模块在动作执行前进行约束修正
3. 在动态障碍环境中兼顾目标到达与碰撞规避

因此：

- `quick-demos/` 适合用来做课程答辩时的快速演示
- `isaac-training/` 适合说明训练流程和任务配置
- `ros1/` 适合展示完整仿真部署链路

## 五、补充说明

- 本仓库当前提交版仅保留 `ROS1`
- 为兼容 Windows 文件系统，`ros1/onboard_detector` 中一个权重文件名已做兼容性调整，代码引用已同步更新
- 如果只需要进行课程验收展示，优先运行 `quick-demos/simple-navigation.py` 即可
