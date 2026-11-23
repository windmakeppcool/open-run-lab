"""
@author: cunyue
@file: __init__.py
@time: 2026/3/11 12:54
@description: SwanLab 运行时类型
"""

from typing import Literal

ResumeType = Literal["must", "allow", "never"]
"""
Run 恢复策略
"""

ParallelType = Literal["none", "shared"]
"""
Run 并行策略
"""

ModeType = Literal["disabled", "offline"]
"""
Run 运行策略

仅在本地运行，不包含任何云端同步模式。

* `offline`: 将实验数据写入本地 swanlog 目录，可通过 swanlab-console 查看。
* `disabled`: 完全关闭 SwanLab，不记录任何数据。
"""

FinishType = Literal["success", "crashed", "aborted"]
"""
Run 结束策略
"""


AsyncLogType = Literal["asyncio", "threading", "spawn", "fork"]
"""
异步日志上报类型
"""

SaveType = Literal["live", "now", "end"]
"""
文件保存策略
"""
