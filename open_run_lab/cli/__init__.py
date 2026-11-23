"""
@author: cunyue
@file: __init__.py
@time: 2026/3/5 14:32
@description: OpenRunLab 命令行交互，在终端运行 `orlab` 命令进行一些CLI操作

纯本地版本，不包含任何云端交互命令。
"""

import click

from open_run_lab.sdk import pkg

from .converter import convert
from .mode import disabled, offline


@click.group(invoke_without_command=True)
@click.version_option(pkg.helper.get_orlab_version(), "--version", "-v", message="OpenRunLab %(version)s")
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
