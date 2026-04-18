# Open-Source Notice

本仓库为课程作业整理版，包含公开开源项目的整理、封装与课程化改造，不构成对上游来源的原创替代声明。

## 保留的开源来源

1. NavRL
   - 原始主题：动态环境中的安全飞行导航
   - 原许可证：MIT
   - 原仓库中顶层 `LICENSE` 已保留

2. OmniDrones
   - 位置：`isaac-training/third_party/OmniDrones`
   - 原许可证：MIT

3. Orbit
   - 位置：`isaac-training/third_party/orbit`
   - 原许可证：BSD-3-Clause

## 本课程项目中的整理与改动

- 重写课程作业版 README 与运行说明
- 增加轻量级动态障碍导航仿真脚本 `scripts/run_lite_sim.py`
- 增加导航任务配置 `SafeUAVNav.yaml`
- 增加单无人机训练用 `ppo.yaml`
- 修复原压缩包中缺失 `third_party/tensordict` 和 `third_party/rl` 后导致的安装脚本失效问题
- 清理与课程提交无关的第三方文档和演示资源

## 说明

本仓库的课程作业包装层与轻量级演示属于新增内容；Isaac Sim 高保真训练部分依然遵守对应第三方代码的原始许可证要求。
