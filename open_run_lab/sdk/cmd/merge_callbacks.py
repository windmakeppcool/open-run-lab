"""
@author: cunyue
@file: merge_callbacks.py
@time: 2026/4/30
@description: open_run_lab.merge_callbacks 方法，合并自定义回调函数
"""

from open_run_lab.sdk.cmd.guard import with_cmd_lock, without_run
from open_run_lab.sdk.internal.context.components.callbacker import global_callbacker
from open_run_lab.sdk.typings.context import CallbacksType

__all__ = ["merge_callbacks"]


@with_cmd_lock
@without_run("merge_callbacks")
def merge_callbacks(callbacks: CallbacksType) -> None:
    """Merge custom callbacks into the global OpenRunLab callback registry.

    This function allows you to register callbacks before initializing a run.
    It must be called before `open_run_lab.init()`.

    :param callbacks: Custom callbacks to merge. Can be a single Callback object or an iterable of Callback objects.

    Examples:

        Merge a single callback:

        >>> import open_run_lab
        >>> from open_run_lab import Callback
        >>> class MyCallback(Callback):
        ...     @property
        ...     def name(self) -> str:
        ...         return "my_callback"
        ...     def on_run_initialized(self, run_dir, path):
        ...         print("Run initialized!")
        >>> open_run_lab.merge_callbacks(MyCallback())
        >>> open_run_lab.init()

        Merge multiple callbacks:

        >>> class AnotherCallback(Callback):
        ...     @property
        ...     def name(self) -> str:
        ...         return "another_callback"
        ...     def on_run_initialized(self, run_dir, path):
        ...         print("Run initialized by another callback!")
        >>> open_run_lab.merge_callbacks([MyCallback(), AnotherCallback()])
        >>> open_run_lab.init()
    """
    global_callbacker.merge_callbacks(callbacks)
