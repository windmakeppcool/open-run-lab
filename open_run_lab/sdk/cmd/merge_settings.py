"""
@author: cunyue
@file: merge_settings.py
@time: 2026/3/6 21:48
@description: open_run_lab.merge_settings 方法，合并自定义配置项
"""

from typing import Union

from open_run_lab.sdk.cmd.guard import with_cmd_lock, without_run
from open_run_lab.sdk.internal.settings import Settings, create_settings, set_global_settings

__all__ = ["merge_settings"]


@with_cmd_lock
@without_run("merge_settings")
def merge_settings(settings: Union[Settings, dict]) -> None:
    """Merge custom settings into the global OpenRunLab configuration.

    This function allows you to customize OpenRunLab's behavior before initializing a run.
    It must be called before `open_run_lab.init()`.

    :param settings: Custom settings to merge. Can be either a Settings object or a dict.

    Examples:

        Merge settings from a dictionary:

        >>> import open_run_lab
        >>> open_run_lab.merge_settings({"mode": "offline", "log_dir": "./my_logs"})
        >>> open_run_lab.init()

        Disable hardware monitoring:

        >>> import open_run_lab
        >>> open_run_lab.merge_settings({"probe": {"monitor": False}})
        >>> open_run_lab.init()

        Use a Settings object:

        >>> import open_run_lab
        >>> from open_run_lab import Settings
        >>> from pathlib import Path
        >>> custom_settings = Settings(mode="offline", log_dir=Path("./experiments"))
        >>> open_run_lab.merge_settings(custom_settings)
        >>> open_run_lab.init()
    """
    global_settings = create_settings()
    global_settings.merge_settings(settings)
    set_global_settings(global_settings)
