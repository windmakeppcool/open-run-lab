"""
@author: cunyue
@file: require.py
@time: 2026/8/11
@description: open_run_lab.require 方法，过渡态用于动态选择 core/probe 后端实现

设计参考 wandb.require，属于中间过渡态 API：
- 默认使用 Python 内置实现（CorePython / ProbePython）
- 在 open_run_lab.init 之前调用 open_run_lab.require(...) 切换后端实现：
  - "core" / "probe"：切换到新后端（Go core / Rust probe）
  - "core_python" / "probe_python"：显式切回 Python 内置实现
- 也可通过环境变量 ORLAB_REQUIRE=core,probe 在导入时生效（应用逻辑见 helper.impl）
- 待新后端成为默认实现后，此 API 将退化为 no-op 或废弃
"""

from typing import List

from open_run_lab.sdk.cmd.guard import with_cmd_lock, without_run
from open_run_lab.sdk.internal.pkg import console, helper

__all__ = ["require"]


@with_cmd_lock
@without_run("require")
def require(*requirements: str) -> List[str]:
    """Enable a transitional OpenRunLab runtime backend (process-global).

    Must be called before ``open_run_lab.init()``. Currently supported requirements:

    - ``"core"``: switch to the OpenRunLab Go core runtime (orlab-core).
    - ``"probe"``: switch to the OpenRunLab Rust probe runtime.
    - ``"core_python"``: explicitly use the built-in Python core.
    - ``"probe_python"``: explicitly use the built-in Python probe.

    Equivalent to setting the ``ORLAB_REQUIRE`` environment variable (comma-separated).
    Idempotent; unknown tokens raise ``ValueError``.

    :param requirements: One or more requirement tokens, e.g. ``"core"``, ``"probe"``.
    :return: The list of activated requirement tokens.
    :raises ValueError: If a requirement token is unknown.
    :raises RuntimeError: If called while a run is active.

    Examples:

        >>> import open_run_lab
        >>> open_run_lab.require("core")
        >>> open_run_lab.init()
    """
    activated: List[str] = []
    for raw in requirements:
        token = raw.strip().lower()
        label = helper.apply_requirement(token)
        console.debug(f"require('{token}') -> {label}")
        activated.append(token)
    return activated
