# OpenRunLab 纯本地部署指南

本项目为 **纯本地运行版本**：不依赖 Docker、云端 API、云数据库、云消息队列或任何第三方远程服务。
SDK 将实验数据写入本地 `orlab-log` 目录，`orlab-console` 前端与后端读取同一目录并在浏览器中展示。

## 1. 依赖清单

| 组件 | 版本要求 | 用途 | 是否必需 |
|---|---|---|---|
| Python | >= 3.9 | 运行 OpenRunLab SDK | 使用 SDK 时必需 |
| Node.js | >= 18 | 运行 `orlab-console` 前后端 | 使用控制台时必需 |
| npm | 随 Node.js 提供 | 安装控制台依赖 | 使用控制台时必需 |

Python 运行时依赖见 `pyproject.toml` 的 `dependencies`（`requests` 仅用于用户自配置的 webhook 通知，默认不触发任何网络请求）。

控制台依赖：

- 后端：`express`、`cors`、`protobufjs`、`yaml`
- 前端：`vue`、`vue-router`、`echarts`

**不需要**：Docker、Kubernetes、PostgreSQL/MySQL、Redis、Kafka、MinIO/S3、Elasticsearch。

## 2. 安装

### 2.1 安装 SDK

```bash
# 在仓库根目录
pip install -e .
```

### 2.2 安装控制台依赖

```bash
cd orlab-console/backend && npm ci
cd ../frontend && npm ci
```

## 3. 环境校验

```bash
bash scripts/check-env.sh
```

校验内容：Python / Node / npm 版本、`protos/` 目录、`orlab-log` 数据目录、控制台依赖是否安装、端口占用。

可选环境变量：

- `ORLAB_LOGDIR`：控制台读取的数据目录，默认 `orlab-console/testdata/orlab-log`
- `ORLAB_PROTOS_DIR`：proto 定义目录，默认仓库根目录 `protos/`
- `PORT`：后端端口，默认 `8787`
- `FRONTEND_PORT`：前端端口，默认 `5173`

## 4. 启动

### 4.1 一键启动

```bash
bash scripts/start-local.sh
```

脚本会先执行环境校验，按需安装缺失的 npm 依赖，然后启动后端并等待 `/api/health` 就绪，再启动前端。

### 4.2 手动启动

```bash
# 终端 1：后端，默认 http://127.0.0.1:8787
cd orlab-console/backend
npm run dev

# 终端 2：前端，默认 http://localhost:5173
cd orlab-console/frontend
npm run dev
```

浏览器打开 <http://localhost:5173>。

## 5. 运行实验（纯本地）

```python
import open_run_lab

open_run_lab.init(
    project="my-project",
    mode="offline",  # 默认值，可省略
    config={"lr": 0.001},
)

for step in range(10):
    open_run_lab.log({"loss": 1.0 / (step + 1), "acc": step / 10})

open_run_lab.finish()
```

- 运行模式仅支持 `offline` 与 `disabled`。
- `offline`：数据写入 `./orlab-log/run-*`，重启控制台后端后即可看到新增实验。
- `disabled`：完全不记录。
- 数据目录可通过 `ORLAB_LOGDIR` 覆盖。

控制台后端在启动时扫描一次 `run-*` 目录；新增或删除实验目录后需重启后端。已扫描实验的数据文件变化后会自动重新解析。

## 6. 数据目录结构

```
orlab-log/
└── run-<timestamp>-<run_id>/
    ├── run-<run_id>.orlab   # LevelDB log 格式的实验记录
    ├── files/               # 配置、元数据、save() 软链接
    ├── media/               # 图片、音频等媒体文件
    └── debug/               # 调试日志
```

## 7. 接口验证

```bash
curl http://127.0.0.1:8787/api/health
curl http://127.0.0.1:8787/api/projects
curl http://127.0.0.1:8787/api/experiments
```

`/api/health` 中的 `runCount` 表示启动时扫描到的实验目录数量。

## 8. 构建产物

```bash
cd orlab-console/backend && npm run build && npm start
cd orlab-console/frontend && npm run build
```

前端使用同源 `/api` 与 history 路由；部署构建产物时需自行配置 `/api` 反向代理与前端路由回退。后端不会托管前端静态文件。

## 9. 安全说明

控制台后端未实现认证或授权，且默认允许任意来源的 CORS。请勿将其直接暴露到不可信网络。

## 10. 与上游的关系

本项目基于 SwanLab 的 Apache-2.0 代码修改与裁剪，并复用了其 SDK 运行时、数据模型、本地存储实现与 protobuf 定义；`orlab-console` 控制台为本项目独立实现。

为保证纯本地运行，本版本移除了依赖闭源/云端服务的组件：

- 云端上传链路（`mode="online"`）与登录、同步、远程 API 相关命令
- 基于闭源 `swanboard` 的本地看板服务与 `mode="local"`
- 官方私有化 `self_hosted` 管理接口

本项目不包含 SwanLab 的闭源组件，与 SwanLab 官方无隶属或背书关系。如需查看数据，请使用本仓库内的 `orlab-console`。完整声明见 [NOTICE](../NOTICE)。
