# 品牌剥离与上游复用声明改造方案

> 状态：**已确认执行**
> 决策：项目名 `open-run-lab` · 清除范围**方案 F（全量清除）** · 品牌素材**直接删除**
> 适用仓库：`/home/lly25782/SwanLab`（基于 SwanLab SDK 的纯本地分支）
> 法务前提：只复用 Apache-2.0 的 SDK 与 `protos/`；**不引入** `SwanHubX/self-hosted`（FSL-1.1）代码、`swanboard` 二进制或云端接口。

## 1. 目标与边界

1. 对外彻底移除 SwanLab 品牌痕迹：名称、logo、截图、作者、链接、徽章、社群入口。
2. 代码标识符、协议包名、磁盘格式全部改为本项目命名，仓库内除 `NOTICE`/`LICENSE`/README 上游声明外不保留 `swanlab` 字样。
3. 在相关位置明确写出"复用 SwanLab（Apache-2.0）逻辑"的范围与修改声明。
4. 改造后构建、单测、控制台前后端构建全部通过。

非目标：不重写 SDK 业务逻辑，只做标识符替换、格式改名与元数据清理。

## 2. 最终命名映射

| 用途 | 取值 |
|---|---|
| 项目展示名 | `OpenRunLab` |
| Python 发行包 | `open-run-lab` |
| Python import / 目录 | `open_run_lab` |
| CLI 命令 / 短前缀 | `orlab` |
| 控制台目录 | `orlab-console` |
| npm 包名 | `orlab-console-backend` / `orlab-console-frontend` |
| proto 包名 | `orlab.<domain>.v1` |
| proto 目录 | `protos/orlab/...` |
| 数据目录默认值 | `./orlab-log` |
| 数据文件后缀 | `.orlab` |
| 文件头魔数 | `:ORL`（uint16 `0xE1D6`、version `2` 不变） |
| 元数据文件 | `files/orlab-metadata.json` |
| 指标前缀 | `__orlab__.` |
| 配置目录 | `.orlab` |
| 探针临时目录前缀 | `.orlab_test_` |
| 环境变量前缀 | `ORLAB_`（如 `ORLAB_LOGDIR`、`ORLAB_WEBHOOK`、`ORLAB_REQUIRE`） |
| Go module | `github.com/open-run-lab/open-run-lab/core` |

GitHub 组织名若与实际不符，执行时统一替换为真实仓库地址，其余不变。

## 3. 全量替换规则（方案 F）

按顺序执行，禁止一次性全局替换：

| 序 | 模式 | 替换为 | 范围 |
|---|---|---|---|
| 1 | 目录 `swanlab/` | `open_run_lab/` | `git mv` |
| 2 | 目录 `swanlab-console/` | `orlab-console/` | `git mv` |
| 3 | 目录 `protos/swanlab/` | `protos/orlab/` | `git mv` |
| 4 | 目录 `core/proto/swanlab/` | 重新生成到 `core/proto/orlab/` | 不手改 |
| 5 | `swanlab.`（proto 包名/类型引用） | `orlab.` | `*.proto`、`proto.ts` |
| 6 | `"swanlab/`（proto import 路径） | `"orlab/` | `*.proto` |
| 7 | `github.com/swanhubx/swanlab/core` | `github.com/open-run-lab/open-run-lab/core` | `go.mod`、`go_package` |
| 8 | `from swanlab` / `import swanlab` | `from open_run_lab` / `import open_run_lab` | Python 源码、测试 |
| 9 | `SWANLAB_` | `ORLAB_` | 环境变量、settings env_prefix、测试 |
| 10 | `swanlog`（目录名/展示文本） | `orlab-log` | 默认值、文档、脚本 |
| 11 | `.swanlab`（后缀/目录/探针前缀） | `.orlab` | store、settings、控制台 reader |
| 12 | `:SWL` | `:ORL` | SDK store、控制台 reader |
| 13 | `swanlab-metadata.json` | `orlab-metadata.json` | SDK、控制台 |
| 14 | `__swanlab__.` | `__orlab__.` | SDK 指标前缀、控制台过滤 |
| 15 | `SwanLab` / `swanlab`（展示文本） | `OpenRunLab` / `orlab` | README、CLI、控制台 UI、日志 |

注意：

- `.swanlab` 替换时必须区分"文件后缀"与"目录名"，二者都改，但不要误伤 `__swanlab__.` 前缀（该条单独处理）。
- 生成物 `open_run_lab/proto/**`、`core/proto/**` 只能由生成脚本产出，禁止手改。
- `uv.lock` 由 `uv lock` 重新生成。

## 4. 需同步修改的配置点

| 文件 | 修改 |
|---|---|
| `pyproject.toml` | `name`、`authors`（换成本项目作者，删除上游邮箱）、`Homepage/Source/Bug Reports/Documentation`、description、keywords、`[project.scripts]` 入口 |
| `open_run_lab/package.json` | `name` + version 保持 |
| `core/go.mod` | module path |
| `protos/**/*.proto` | `package`、`import`、`go_package`、注释中的 SwanLab 文案 |
| `scripts/generate_protos.py` | 输出目录、import 修复正则、Go module 路径 |
| `orlab-console/backend/src/swanlab/` | 目录改名为 `src/orlab/`；`proto.ts` 的 `PROTO_FILES`、`lookupType("orlab.record.v1.Record")`、`ORLAB_PROTOS_DIR` |
| `orlab-console/backend/src/index.ts` | `ORLAB_LOGDIR`、日志文案、默认目录 |
| `orlab-console/frontend/**` | 包名、页面标题、页脚声明、`__orlab__.` 过滤、设计稿引用 |
| `scripts/check-env.sh`、`scripts/start-local.sh` | 目录名、环境变量、提示文案 |
| `Makefile` | 包路径、构建产物路径 |
| `.github/workflows/*` | 包名、PyPI 地址、飞书文案；删除上游发布通知或改为本项目 |
| `.github/ISSUE_TEMPLATE/*` | 删除 `swanlab.cn` 全部链接 |
| `tests/**` | import、环境变量、目录名断言；重命名含 `swanlab` 的测试文件 |
| `AGENTS.md`、`docs/skills/**` | 路径与文案同步（AGENTS.md 虽被 gitignore，仍须与实际一致） |

## 5. 复用声明落点

### 5.1 新增 `NOTICE`（仓库根目录）

```text
OpenRunLab
Copyright 2026 <YOUR_NAME_OR_ORG>

This product includes software developed as SwanLab
(https://github.com/SwanHubX/SwanLab),
Copyright 2024-2025 Emotion Machine (Beijing) Technology Co., Ltd.,
licensed under the Apache License, Version 2.0.

Reused and modified from SwanLab (Apache-2.0):
- Python SDK runtime, data model and local store implementation
- Protocol definitions under protos/
- Converter, integration and plugin modules

Independent implementation:
- orlab-console/ (local read-only console) is written for this project
  and does not include SwanLab's closed-source components
  (swanboard, self-hosted service, or cloud services).

"SwanLab" is a trademark of its owner. This project is not affiliated
with or endorsed by Emotion Machine (Beijing) Technology Co., Ltd.
```

### 5.2 `LICENSE`

保留首行原版权，追加修改方版权：

```text
Copyright 2024-2025 Emotion Machine (Beijing) Technology Co., Ltd.
Modifications Copyright 2026 <YOUR_NAME_OR_ORG>
```

### 5.3 README "上游与许可"章节

> 本项目基于 [SwanLab](https://github.com/SwanHubX/SwanLab) 的 Apache-2.0 代码进行修改与裁剪，复用了其 SDK 运行时、数据模型、本地存储实现与 protobuf 定义；本地控制台为本项目独立实现。本项目**不包含** SwanLab 的闭源组件（swanboard、私有化服务、云服务），与 SwanLab 官方无隶属或背书关系。完整声明见 [NOTICE](NOTICE)。

`README_EN.md` 同步英文版本。

### 5.4 其他

- `docs/LOCAL_DEPLOYMENT.md` 第 10 节改为"与上游的关系"。
- `CONTRIBUTING.md` 声明本项目非官方仓库。
- 控制台页脚新增 `Based on SwanLab (Apache-2.0) · Not affiliated`。

## 6. 执行顺序（子代理按阶段执行，每阶段验证后再进入下一阶段）

### 阶段 A：元数据与核心重命名

1. `pyproject.toml`、`open_run_lab/package.json`、`core/go.mod`、两个 npm `package.json`。
2. `git mv swanlab open_run_lab`、`git mv swanlab-console orlab-console`、`git mv protos/swanlab protos/orlab`。
3. Python import、CLI 入口、`--version` 文案。
4. 环境变量前缀（settings、compat、integration、cli、测试）。
5. 磁盘格式常量（后缀、魔数、metadata、指标前缀、配置目录、探针前缀）。
6. proto：改 `package`/`import`/`go_package`/注释 → 改 `scripts/generate_protos.py` → 重新生成 Python proto → 同步 `core/proto`。
7. 脚本、Makefile、CI、issue 模板中的路径与变量。

验证：

```bash
python3 -c "import open_run_lab; print(open_run_lab.__version__)"
python3 -m open_run_lab --version || python3 -c "from open_run_lab.cli import cli; cli(['--version'])"
python3 -m pytest tests/unit -q   # 基线：1 failed(torch 缺失) / 1457 passed / 25 skipped
```

> Go 工具链若不可用：`core/proto` 无法重新生成时，禁止手改 `.pb.go`；在阶段报告中列出未完成项，并保留 `make proto` 说明。

### 阶段 B：控制台与样例数据

1. `orlab-console/backend`：目录 `src/swanlab` → `src/orlab`，import、`PROTO_FILES`、`lookupType`、env（`ORLAB_LOGDIR`、`ORLAB_PROTOS_DIR`）、日志文案。
2. `orlab-console/frontend`：包名、标题、页脚声明、`__orlab__.` 过滤、注释中的设计稿路径。
3. 删除旧 `testdata/swanlog`，用新 SDK 重新生成样例数据到 `testdata/orlab-log`（同步 `generate_sample_data.py` 与后端默认路径）。
4. 构建验证：

```bash
cd orlab-console/backend && npm run build
cd ../frontend && npm run build
```

### 阶段 C：文档与素材

1. 删除 `readme_files/swanlab-*`、`.trae-html-share-packages/swanlab-console-design.html.zip`。
2. `swanlab-console-design.html` → `orlab-console-design.html`，清除品牌文案。
3. 重写 README 中英：去掉 logo/在线版/文档/社群/Star History/contributors/徽章/演示视频/上游案例链接；新增"上游与许可"。
4. `CONTRIBUTING.md`、`SECURITY.md`、`CODE_OF_CONDUCT.md`、`docs/LOCAL_DEPLOYMENT.md`、`AGENTS.md`、`docs/skills/**`。
5. 新增 `NOTICE`，修改 `LICENSE`。

### 阶段 D：全量验收

```bash
# 1. 残留检查：除 NOTICE/LICENSE/README 声明外应为 0
grep -rni "swanlab" . --exclude-dir=.git --exclude-dir=node_modules --exclude-dir=.venv --exclude-dir=dist

# 2. Python
python3 -m pytest tests/unit -q

# 3. CLI
python3 -c "from open_run_lab.cli import cli; cli(['--version'])"

# 4. 控制台
cd orlab-console/backend && npm run build && cd ../frontend && npm run build && cd ../..

# 5. 本地部署
bash scripts/check-env.sh

# 6. Go（若工具链可用）
cd core && go build ./... && cd ..
```

## 7. 环境现状与前置

- 系统 Python 3.13 已具备 SDK 运行依赖，可直接 `python3 -m pytest`。
- 基线测试：**1 failed（缺 torch）/ 1457 passed / 25 skipped**，改造后应保持一致。
- 无 `protoc`、无 Go 工具链。Python proto 需先安装 `grpcio-tools`（`python3 -m pip install grpcio-tools`）；Go proto 需要 Go + `protoc-gen-go`，缺失时按阶段 A 说明处理。
- 控制台 `node_modules` 已安装，可直接 `npm run build`。

## 8. 明确不做

- 不反编译 `swanboard`、不抓取 `swanlab.cn` 接口、不复制其 UI 像素稿与文案。
- 不引入 `SwanHubX/self-hosted` 的任何代码。
- 不做与本次改造无关的重构、格式化或注释清理。
- 不保留上游作者邮箱、社群二维码、Star History、PyPI 徽章。
