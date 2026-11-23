# SwanLab 领域审核契约

先根据 PR 文件列表判断适用范围，只读取与变更相关的章节。所有 Python 应用代码还需检查“横切质量与代码规范”；涉及凭据、网络、日志、文件路径或用户数据时，再检查“安全与隐私”。

未命中具体章节的变更仍需结合调用关系、相邻模块和测试判断。本文没有定义的项目契约不得自行推断为硬性规则。

## 公共 API 与类型兼容

适用路径：`swanlab/__init__.py`、`swanlab/__init__.pyi`、`swanlab/sdk/__init__.py`、`swanlab/sdk/typings/**`、`swanlab/sdk/protocol/**`、`swanlab/exceptions.py`、`swanlab/deprecated/**` 及公开类和函数。

- 顶层运行时导出、`__all__` 和 `swanlab/__init__.pyi` 保持同步。
- 新增或修改公开参数时检查默认值、返回值、异常、文档和类型签名是否一致。
- 已发布 API 的删除、重命名或语义变化需要兼容或明确的弃用路径，不能静默破坏用户代码。
- 保持 Python 3.9-3.14 可用，不引入只在单一 Python 版本成立的行为。
- 修改 `swanlab.run`、`get_run()` 等动态属性时覆盖初始化前、运行中和结束后的行为。

## Run 生命周期与运行时组件

适用路径：`swanlab/sdk/cmd/**`、`swanlab/sdk/internal/run/**`、`swanlab/sdk/internal/context/**`、`swanlab/sdk/internal/bus/**`、`swanlab/sdk/internal/impl.py`。

- `init`、`log`、`finish` 和 reinit 的状态转换清晰，失败路径不会遗留半初始化的全局状态。
- `offline`、`disabled` 两种模式保持各自边界；disabled 模式不应产生不必要的文件副作用。
- 运行时组件按依赖顺序启动、按反向顺序停止；停止时先完成异步任务和末尾事件，再关闭消费者。
- terminal proxy、后台线程、executor、watcher、signal 和 atexit hook 都有确定的安装与清理路径。
- 主线程、非主线程、fork/spawn、异常退出和重复 finish 场景不能死锁、重复上传或丢失数据。
- 修改全局或上下文状态时检查多线程和 asyncio 隔离。

## Record、Core 与本地存储

适用路径：`swanlab/sdk/internal/core_python/**`、`store/**`、Record builder 和 consumer。

- Record 保持可顺序写入、读取和重放；序号、批次和完成状态不能倒退或重复计数。
- scalar、media、column、config、log、save 和生命周期记录的转换链路保持完整。
- 所有记录只写入本地 store，不引入网络上传、远程重试或云端队列逻辑。
- 成功、部分失败和最终失败时，buffer、落盘状态与返回结果保持一致。
- 批处理、队列和并发写入应有边界，避免大数据量下无界内存、忙等、锁竞争或线程泄漏。
- 文件与媒体写入检查 Windows/POSIX 路径、符号链接逃逸、重复写入和幂等行为。

## 配置与 Settings

适用路径：`swanlab/sdk/internal/settings/**`。

- 保持 Settings 声明的配置源优先级；有意调整时同步兼容测试和用户文档。
- Settings 负责类型、格式和默认值；目录创建等业务副作用留在初始化阶段。
- `merge_settings` 只合并用户显式设置字段，嵌套配置不能被意外整块覆盖。
- 环境变量、YAML 和 Secret 文件的回退关系明确；不引入 API host、API key、netrc 或远程认证配置。
- 日志和异常不能暴露 Secret 或用户敏感配置。

## CLI

适用路径：`swanlab/cli/**`、`swanlab/sdk/cmd/**`。

- 只支持 offline/disabled 两种模式；不提供 login、logout、verify、sync、ping、api、watch 等命令。
- CLI 的参数名、别名、默认值、帮助文本、输出和退出码保持兼容。
- 非交互环境不能意外等待输入；命令输出中的实验位置指向本地 `swanlog` 目录。

## 媒体、转换与文件

适用路径：`swanlab/sdk/internal/run/transforms/**`、媒体类型、`save`、文件 watcher 和上传逻辑。

- Image、Audio、Video、Text、Html、ECharts、Object3D、Molecule 的输入类型、输出文件和 Record 元数据一致。
- 可选依赖应按需加载；未安装媒体或框架依赖时不能影响基础 `import swanlab`。
- 文件名、扩展名、MIME、大小、hash、caption 和 step 在转换与本地写入链路中不丢失。
- 文件句柄、临时文件、watcher、线程和大对象有释放路径。
- 大文件和批量媒体避免一次性读入内存，并遵守本地存储的大小、分片和批次限制。
- `save` 的 glob、base path、符号链接和跨平台路径不能越过预期边界或写入错误文件。

## 硬件与环境探测

适用路径：`swanlab/sdk/internal/probe_python/**`（含 `hardware_vendor/**`、`monitor/**`、`environment/**`、`protocol/**`）、`swanlab/vendor/**`。

- 第三方厂商 SDK、驱动或命令行工具缺失时降级为“不可用”，不能让 `import swanlab` 或 `init` 失败。
- 厂商探测按已有约定判定可用性；探测失败、超时和权限不足都走统一的失败路径，不打断 Run。
- 监控线程有明确的启动、采样间隔和停止路径；Run finish 后不残留线程或子进程。
- 采集结果的字段名、单位和数据类型保持稳定，避免破坏本地控制台已有的硬件面板。
- 探测调用外部命令时限制超时、不拼接不可信输入，且不在日志中输出完整命令输出。
- 环境采集（git、conda、requirements、runtime）只收集产品需要的信息；参见“安全与隐私”。
- 探测层直接调用 Core，不经事件总线；改动时确认写入时机仍在 Run 就绪之后。
- 新增厂商时补充无依赖环境下的隔离测试，不依赖真实硬件。

## 共享工具与内部 pkg

适用路径：`swanlab/sdk/internal/pkg/**`（`safe/`、`fs/`、`console/`、`fork/`、`timer/`、`executor/`、`scope/`、`adapter/`、`constraints/`、`helper/` 等）、`swanlab/utils/**`。

- 这些是被多层复用的公共工具，改动前确认全部调用点，评估影响范围而不只看本地语义。
- `safe` 系列的错误吞噬边界保持明确；不要用它掩盖应当上抛的错误，也不要留空 catch。
- 文件、路径和控制台工具保持 Windows/POSIX 与编码兼容，不假设 UTF-8 终端或 POSIX 路径分隔符。
- 线程、executor、timer 和 scope 工具的资源在异常路径同样释放；不引入全局可变状态。
- 工具函数保持无副作用和可测试；导入期不做网络、文件写入或线程启动。
- 修改共享工具时同步更新既有单测，并覆盖调用方的关键路径。

## 集成、转换器与插件

适用路径：`swanlab/integration/**`、`swanlab/converter/**`、`swanlab/plugin/**`。

- 第三方框架未安装时保持基础包可导入，并提供清晰错误而非导入期崩溃。
- 框架 callback 只在正确进程或 rank 记录，避免重复初始化、重复 step 和重复 finish。
- monkey patch 保留原库行为，重复调用尽量幂等，并明确安装时机和生命周期。
- 第三方配置和指标转换保留关键字段、step、命名空间和数据类型。
- callback 的异步任务在 Python shutdown 和 Run finish 时不会静默丢失。
- 新增集成或插件时补充对应隔离测试，不依赖真实外部服务。

## Protobuf 与生成代码

适用路径：`protos/**`、`swanlab/proto/**`、`core/proto/**`、`scripts/generate_protos.py`。

- `protos/**` 是协议源；变更后同步提交 Python 和 Go 生成代码。
- 已发布 `v1` 消息保持向后兼容，不复用或改变已有字段号和枚举值语义。
- Record 顶层信封和 append-only 日志保持旧记录可解析、可跳过未知字段。
- 媒体和文件仍通过路径与元数据引用，不把大二进制意外内联进 Record。
- 修改生成脚本时检查导入路径修复、`.pyi` 生成和 package `__init__.py`。

## 构建、依赖与发布

适用路径：`pyproject.toml`、`uv.lock`、`Makefile`、`swanlab/package.json`、`.github/workflows/**`。

- 依赖变更同步 `pyproject.toml` 与 `uv.lock`，区分核心依赖、dev dependency 和 optional extra。
- 基础安装不能强制引入只服务于单个媒体类型或第三方框架的重依赖。
- wheel 包含公共 stub、Proto 和运行时所需资源；版本仍由既定单一来源读取。
- 发布和构建修改检查 tag 解析、版本写入、wheel 产物和 PyPI/GitHub Release 流程。
- 保持 Linux、Windows、macOS 与 Python 3.9-3.14 的语法、路径、编码和依赖兼容。

## 测试与验证

适用路径：`tests/**`、pytest 配置和 CI workflow。

- 行为变更应在对应 `tests/unit` 路径增加回归测试，测试目录与源码模块尽量对应。
- 默认使用 mock、`tmp_path` 和 disabled/offline 模式隔离真实网络、用户凭据和全局文件。
- 生命周期、并发、重试、跨平台路径和兼容性变更同时覆盖成功与失败路径。
- 测试清理全局 Settings、Run、环境变量、线程、patch 和文件，避免依赖执行顺序。
- 本地验证结果不能替代 CI 的操作系统和 Python 版本矩阵。

## 横切质量与代码规范

适用路径：所有 Python 代码、配置和依赖变更。

- 从正确性、兼容性、可读性、架构、安全和性能判断具体回归，不以个人偏好提出 finding。
- 以 `pyproject.toml` 中 Ruff、basedpyright 和 pytest 配置为准，不另造格式规则。
- 新代码保持类型清晰；`Any`、`cast`、`type: ignore` 和宽泛异常必须有具体理由和最小作用域。
- 避免导入期网络、文件写入、线程启动和重型可选依赖加载。
- 资源获取与释放成对；异常路径不能跳过锁释放、context reset、线程停止或文件关闭。
- 不新增调试输出、临时分支、无用 import 或由本次变更产生的死代码。
- 复杂度是审查信号而非机械行数门禁；优先最小正确改动，不为单一用例增加抽象层。

## 安全与隐私

适用条件：凭据、认证、网络、日志、HTML、文件路径、上传、环境探测或用户数据发生变化。

- Secret 和密码不写入日志、异常或测试快照。
- 配置文件和 Secret 文件遵守最小权限，不能写入错误用户目录。
- 自定义 webhook 和外部 URL 检查协议、凭据发送范围、重定向和 SSRF 风险。
- HTML、终端日志、配置和第三方框架数据视为不可信输入，在本机展示前保持明确的安全边界。
- `save` 和解压/复制逻辑防止路径穿越、符号链接逃逸和任意文件覆盖。
- 环境与硬件探测只采集产品需要的数据，不写入本地敏感路径、环境变量值或用户私有内容。
