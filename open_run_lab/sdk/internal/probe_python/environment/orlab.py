"""
@author: cunyue
@file: orlab.py
@time: 2026/4/24 12:52
@description: OpenRunLab 信息采集模块
"""

from open_run_lab.sdk.internal.pkg import safe
from open_run_lab.sdk.internal.pkg.helper import get_orlab_version
from open_run_lab.sdk.internal.probe_python.context import ProbeContext
from open_run_lab.sdk.internal.probe_python.typings import OrlabSnapshot


@safe.decorator(level="debug", message="Failed to get orlab environment")
def get(ctx: ProbeContext) -> OrlabSnapshot:
    """获取 OpenRunLab 信息快照"""
    run_dir = str(ctx.config.run_dir) if ctx.config.run_dir is not None else None
    return OrlabSnapshot(version=get_orlab_version(), run_dir=run_dir)
