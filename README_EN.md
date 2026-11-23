# OpenRunLab

A local-first tracking and visualization platform for AI training experiments.

OpenRunLab records training metrics and hyperparameters, visualizes media data, and manages and compares experiments. Experiment data is written to local disk by default and viewed through the bundled `orlab-console`; no cloud service is required.

[中文](README.md) / [English](README_EN.md)

## Features

- **Local storage**: Runs are written to a local `orlab-log` directory, never to a remote service, making backup, migration, and offline viewing straightforward.
- **Metric visualization**: Track scalars, hyperparameters, and metric summaries, and inspect curves and tables in the console.
- **Media logging**: Supported metadata types include images, audio, text, video, 3D point clouds, molecular structures, and custom ECharts.
- **Framework integrations**: Callback-based integrations for common training and machine-learning frameworks, with minimal changes to your training code.
- **Notification plugins**: Lark, DingTalk, WeCom, Slack, Discord, Telegram, email, Bark, and a CSV writer.
- **Migration and conversion**: Import historical experiment data from Weights & Biases, TensorBoard, and MLflow.
- **Local console**: The repository ships `orlab-console` (backend + frontend) for fully offline dashboard viewing and experiment management.
- **Run resumption**: Append new metrics to an existing run after training is interrupted or completed.

## Installation

```bash
pip install -e .
```

Installing from source requires Python >= 3.9. The console requires Node.js >= 18 and npm.

## Quick Start

```python
import open_run_lab

# Initialize a run (offline by default; data goes to ./orlab-log)
open_run_lab.init(
    project="my-first-ml",
    config={"learning-rate": 0.003},
)

# Log metrics
for i in range(10):
    open_run_lab.log({"loss": i, "acc": i})

open_run_lab.finish()
```

Once the script finishes, the run data is written to `orlab-log/run-*`; open the local console to inspect it.

### Run modes

- `mode="offline"` (default): data is written to the local `orlab-log` directory.
- `mode="disabled"`: recording is fully disabled and no file side effects are produced.

The data directory can be customized with the `ORLAB_LOGDIR` environment variable.

## Local Console

```bash
# Terminal 1: backend (http://127.0.0.1:8787 by default)
cd orlab-console/backend && npm ci && npm run dev

# Terminal 2: frontend (http://localhost:5173 by default)
cd orlab-console/frontend && npm ci && npm run dev
```

Or use the one-click script from the repository root:

```bash
bash scripts/start-local.sh
```

Environment check script:

```bash
bash scripts/check-env.sh
```

The backend scans the run directories under `orlab-log` once at startup; restart it after adding or removing a run directory. See [docs/LOCAL_DEPLOYMENT.md](docs/LOCAL_DEPLOYMENT.md) for details.

## Data Directory Layout

```
orlab-log/
└── run-<timestamp>-<run_id>/
    ├── run-<run_id>.orlab   # Run records in LevelDB log format
    ├── files/               # Config, metadata, save() links
    ├── media/               # Images, audio, and other media
    └── debug/               # Debug logs
```

## Supported Integrations

The following frameworks and tools can be connected through callbacks, plugins, or migration (names only):

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

## Upstream & License

This project is based on [SwanLab](https://github.com/SwanHubX/SwanLab)'s Apache-2.0 code, with modifications and trimming. It reuses SwanLab's SDK runtime, data model, local store implementation, and protobuf definitions; the local console is an independent implementation of this project. This project **does not include** SwanLab's closed-source components (swanboard, self-hosted service, or cloud services), and it is not affiliated with or endorsed by the SwanLab project. See [NOTICE](NOTICE) for the full statement.

## License

This project is released under the [Apache-2.0](LICENSE) license. See [NOTICE](NOTICE) for copyright and reuse statements.
