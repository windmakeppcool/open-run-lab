"""
@author: cunyue
@file: __init__.py
@time: 2026/4/21 15:25
@description: OpenRunLab 系统监控模块
"""

from typing import Optional

from open_run_lab.sdk.internal.pkg import helper
from open_run_lab.sdk.protocol import CoreProtocol, ProbeProtocol


def create_probe(core: Optional[CoreProtocol] = None, disabled: bool = False) -> ProbeProtocol:
    """core对象工厂

    :param ctx: 运行上下文，包含配置信息和运行时状态
    """
    if helper.get_probe_impl() == "python":
        from open_run_lab.sdk.internal.probe_python import ProbePython

        return ProbePython(core, disabled)
    else:
        # TODO: Core 微服务无感接入
        raise NotImplementedError("The OpenRunLab Rust probe runtime is not available yet.")
