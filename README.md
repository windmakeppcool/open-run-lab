# OpenRunLab

面向 AI 训练实验的本地优先记录与可视化平台。

OpenRunLab 提供训练指标与超参数记录、媒体数据可视化、实验管理与对比能力。所有实验数据默认只写入本地磁盘，通过仓库自带的 `orlab-console` 控制台查看，无需任何云端服务。

[中文](README.md) / [English](README_EN.md)

## 特性

- **本地存储**：实验数据写入本地 `orlab-log` 目录，不经过远程服务，便于备份、迁移与离线查看。
- **指标可视化**：记录标量、超参数、指标总结，并在控制台中查看曲线与表格。
- **媒体记录**：支持图像、音频、文本、视频、3D 点云、生物化学分子、ECharts 自定义图表等元数据类型。
- **框架集成**：为常见训练与机器学习框架提供回调集成，无需大幅改动训练代码。
- **通知插件**：支持飞书、钉钉、企业微信、Slack、Discord、Telegram、邮件、Bark 等通知，以及 CSV 记录器。
- **迁移转换**：可从 Weights & Biases、TensorBoard、MLflow 导入历史实验数据。
- **纯本地控制台**：仓库自带 `orlab-console` 前后端，完全离线查看仪表盘与管理实验。
- **断点续训记录**：支持在训练中断或完成后，向同一实验追加新的指标数据。

## 安装

```bash
pip install -e .
```

源码安装需要 Python >= 3.9。控制台需要 Node.js >= 18 与 npm。

## 快速开始

```python
import open_run_lab

# 初始化一个实验（默认 offline，数据写入 ./orlab-log）
open_run_lab.init(
    project="my-first-ml",
    config={"learning-rate": 0.003},
)

# 记录指标
for i in range(10):
    open_run_lab.log({"loss": i, "acc": i})

open_run_lab.finish()
```

运行结束后，实验数据会写入当前目录下的 `orlab-log/run-*`，打开本地控制台即可查看。

### 运行模式

- `mode="offline"`（默认）：数据写入本地 `orlab-log` 目录。
- `mode="disabled"`：完全关闭记录，不产生文件副作用。

数据目录可通过环境变量 `ORLAB_LOGDIR` 覆盖。

## 本地控制台

```bash
# 终端 1：后端（默认 http://127.0.0.1:8787）
cd orlab-console/backend && npm ci && npm run dev

# 终端 2：前端（默认 http://localhost:5173）
cd orlab-console/frontend && npm ci && npm run dev
```

也可以使用仓库根目录的一键启动脚本：

```bash
bash scripts/start-local.sh
```

环境校验脚本：

```bash
bash scripts/check-env.sh
```

控制台在启动时扫描一次 `orlab-log` 下的实验目录；新增或删除实验目录后需重启后端。详细说明见 [docs/LOCAL_DEPLOYMENT.md](docs/LOCAL_DEPLOYMENT.md)。

## 数据目录结构

```
orlab-log/
└── run-<timestamp>-<run_id>/
    ├── run-<run_id>.orlab   # LevelDB log 格式的实验记录
    ├── files/               # 配置、元数据、save() 软链接
    ├── media/               # 图片、音频等媒体文件
    └── debug/               # 调试日志
```

## 支持的集成

以下框架或工具可通过回调、插件或迁移功能接入（仅列名称）：

- PyTorch
- HuggingFace Transformers
- HuggingFace Accelerate
- PyTorch Lightning
- Torchtune
- Keras
- fastai
- MMEngine
- Ultralytics
- Ray
- PaddleNLP
- LightGBM
- XGBoost
- CatBoost
- Stable-Baselines3
- TensorBoard
- Weights & Biases
- MLflow

## 上游与许可

本项目基于 [SwanLab](https://github.com/SwanHubX/SwanLab) 的 Apache-2.0 代码进行修改与裁剪，复用了其 SDK 运行时、数据模型、本地存储实现与 protobuf 定义；本地控制台为本项目独立实现。本项目**不包含** SwanLab 的闭源组件（swanboard、私有化服务、云服务），与 SwanLab 官方无隶属或背书关系。完整声明见 [NOTICE](NOTICE)。

## 许可证

本项目以 [Apache-2.0](LICENSE) 许可发布，版权与复用声明见 [NOTICE](NOTICE)。
