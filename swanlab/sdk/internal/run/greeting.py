"""
@author: cunyue
@file: greeting.py
@time: 2026/4/28 13:36
@description: 用于在终端打印run运行开始、结束的提示信息
"""

from typing import TYPE_CHECKING

from rich.text import Text

from swanlab.sdk.internal.context import RunContext
from swanlab.sdk.internal.pkg import console
from swanlab.sdk.internal.pkg.helper.version import get_swanlab_version

if TYPE_CHECKING:
    from swanlab.sdk.internal.run import Run

__all__ = ["welcome", "goodbye"]


def _print_version():
    version = get_swanlab_version()
    console.info("Tracking run with swanlab version", version)


def _print_save_dir(ctx: RunContext):
    # skip_store 下本地不再创建 swanlog 日志目录，所有数据都不会落盘
    if ctx.config.settings.core.skip_store:
        console.info("⚠️ ", Text("Local record store disabled; no data will be saved", "yellow"))
        return
    console.info("💾 Run data saved at", Text(str(ctx.config.run_dir), "magenta bold"))


def _print_offline_tip(ctx: RunContext):
    console.info(
        "📊 Run",
        Text("`swanlab-console`", "bold"),
        "to view this run, see docs/LOCAL_DEPLOYMENT.md for local startup instructions.",
    )


def welcome(ctx: RunContext, run: "Run"):
    """
    实验开始欢迎语
    0. Disabled: 直接返回
    1. Offline: 打印版本号、运行日志存储位置
    """
    _ = run
    mode = ctx.config.settings.mode
    if mode == "disabled":
        return
    _print_version()
    _print_save_dir(ctx)
    _print_offline_tip(ctx)


def goodbye(ctx: RunContext, run: "Run"):
    _ = run
    mode = ctx.config.settings.mode
    if mode == "disabled":
        return
    _print_offline_tip(ctx)
