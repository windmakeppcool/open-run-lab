"""
@author: cunyue
@file: __init__.py
@time: 2026/3/5 14:32
@description: SwanLab 命令行交互，在终端运行 `swanlab` 命令进行一些CLI操作

纯本地版本，不包含任何云端交互命令。
"""

import click

from swanlab.sdk import pkg

from .converter import convert
from .mode import disabled, offline


@click.group(invoke_without_command=True)
@click.version_option(pkg.helper.get_swanlab_version(), "--version", "-v", message="SwanLab %(version)s")
@click.pass_context
def cli(ctx):
    if ctx.invoked_subcommand is None:
        click.echo(ctx.get_help())


# ---------------------------------- 注册子命令 ----------------------------------
# Converter
# noinspection PyTypeChecker
cli.add_command(convert)

# Mode
# noinspection PyTypeChecker
cli.add_command(offline)
# noinspection PyTypeChecker
cli.add_command(disabled)

__all__ = ["cli"]
