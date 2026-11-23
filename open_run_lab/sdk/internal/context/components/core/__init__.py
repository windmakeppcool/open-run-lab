"""
@author: cunyue
@file: __init__.py
@time: 2026/4/16 22:30
@description: OpenRunLab 核心模块
"""

from typing import TYPE_CHECKING

from open_run_lab.sdk.internal.pkg import helper
from open_run_lab.sdk.protocol import CoreProtocol

if TYPE_CHECKING:
    from open_run_lab.sdk.internal.context import RunContext


def create_core(ctx: "RunContext") -> CoreProtocol:
    """core对象工厂

    :param ctx: 运行上下文，包含配置信息和运行时状态
    """
    if helper.get_core_impl() == "python":
        from open_run_lab.sdk.internal.core_python import CorePython

        return CorePython(mode=ctx.config.settings.mode)
    else:
        # TODO: Core 微服务无感接入
        raise NotImplementedError("The OpenRunLab Go core runtime is not available yet.")
