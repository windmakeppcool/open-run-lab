"""
@author: cunyue
@file: __init__.py
@time: 2026/3/13

@description: SwanLab Core Python 版本，纯本地数据持久化实现，包括：
1. 将指标、日志、文件记录写入本地 swanlog 存储。
2. 存储指标上下文，便于分布式训练时的指标同步。
...

实现 CoreProtocol，当前为纯 Python 实现。
未来由 swanlab-core（Go 二进制）替代时，此模块整体被替换，
BackgroundConsumer 等调用方无需修改。
"""

from .core import CorePython

__all__ = ["CorePython"]
