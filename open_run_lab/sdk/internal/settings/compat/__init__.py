"""
遗留环境变量兼容层。

集中收纳 settings 各域中通过 default_factory 直接读取 ``os.environ`` 的遗留环境变量
（0.7.x 及以前的命名，与 pydantic-settings 字段映射不对应），
统一经 :func:`open_run_lab.sdk.internal.settings.compat.env.getenv` 剥离 shell 注入的成对引号。

按域拆分为子模块，将来移除遗留支持时可整体删除本包：
- ``env``: 引号剥离与读取工具
- ``experiment``: 实验域（ORLAB_PROJ_NAME/ORLAB_WORKSPACE/ORLAB_EXP_NAME 等）
- ``core``: Core 域（ORLAB_SECTION_RULE_IDX）
- ``integration``: 集成域（ORLAB_WEBHOOK* 等）
"""

from pathlib import Path

from .core import section_rule_index_factory
from .env import getenv, strip_env_quotes
from .experiment import (
    experiment_color_factory,
    experiment_description_factory,
    experiment_group_factory,
    experiment_job_type_factory,
    experiment_name_factory,
    experiment_tags_factory,
    map_resume_value,
    project_name_factory,
    project_public_factory,
    run_id_factory,
    run_resume_factory,
    workspace_factory,
)
from .integration import (
    webhook_timeout_factory,
    webhook_url_factory,
    webhook_value_factory,
)

__all__ = [
    "experiment_color_factory",
    "experiment_description_factory",
    "experiment_group_factory",
    "experiment_job_type_factory",
    "experiment_name_factory",
    "experiment_tags_factory",
    "getenv",
    "log_dir_factory",
    "map_resume_value",
    "project_name_factory",
    "project_public_factory",
    "run_id_factory",
    "run_resume_factory",
    "section_rule_index_factory",
    "strip_env_quotes",
    "webhook_timeout_factory",
    "webhook_url_factory",
    "webhook_value_factory",
    "workspace_factory",
]


def log_dir_factory() -> Path:
    # 向下兼容旧版本环境变量
    return Path(getenv("ORLAB_LOGDIR", str(Path.cwd() / "orlab-log")))
