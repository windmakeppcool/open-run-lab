"""
@author: caddiesnew
@file: __init__.py
@time: 2026/4/1 16:10
@description: CLI Mode 模块：设置默认运行模式 (disabled / offline)

纯本地版本，不提供任何云端同步模式。
"""

import click

from open_run_lab.sdk import Settings, pkg
from open_run_lab.sdk.internal.pkg import console


# noinspection PyShadowingNames
def _save_settings(settings: Settings, local: bool):
    """
    将设置保存到文件中
    """
    if local:
        pwd = Settings.get_pwd_config_dir()
        pkg.helper.mkdir_and_append_gitignore(pwd)
        settings.save_to_yaml(pwd, "mode")
    else:
        user = Settings.get_user_config_dir()
        pkg.fs.safe_mkdir(user)
        settings.save_to_yaml(user, "mode")


# noinspection PyShadowingNames
@click.command()
@click.option("--local", is_flag=True, help="Only disable OpenRunLab for current directory.")
def disabled(local: bool):
    """Disable OpenRunLab."""
    _save_settings(settings=Settings(mode="disabled"), local=local)

    if local:
        console.info("OpenRunLab disabled for this directory.")
    else:
        console.info("OpenRunLab disabled globally.")


# noinspection PyShadowingNames
@click.command()
@click.option("--local", is_flag=True, help="Only set offline mode for current directory.")
def offline(local: bool):
    """Use offline mode for OpenRunLab."""
    _save_settings(settings=Settings(mode="offline"), local=local)

    if local:
        console.info(
            "OpenRunLab offline. Running your script from this directory will only write metadata locally. "
            "Use `orlab disabled --local` to completely turn off OpenRunLab for this directory."
        )
    else:
        console.info(
            "OpenRunLab offline. Running your script will only write metadata locally. "
            "Use `orlab disabled` to completely turn off OpenRunLab."
        )


__all__ = ["disabled", "offline"]
