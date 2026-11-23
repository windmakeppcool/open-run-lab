"""
@author: cunyue
@file: __init__.py
@time: 2026/3/5 14:35
@description: OpenRunLab SDK，负责OpenRunLab库的核心指标上传功能
"""

from open_run_lab.sdk.internal.run.components.config import config

from .cmd import utils as cmd_utils
from .cmd.init import init
from .cmd.merge_callbacks import merge_callbacks
from .cmd.merge_settings import merge_settings
from .cmd.require import require
from .cmd.run import (
    async_log,
    define_metric,
    finish,
    log,
    log_audio,
    log_echarts,
    log_histogram,
    log_html,
    log_image,
    log_molecule,
    log_object3d,
    log_text,
    log_video,
    save,
)
from .internal import impl, pkg
from .internal.run import Run, clear_run, get_run, has_run, set_run
from .internal.run.transforms import (
    Audio,
    ECharts,
    Histogram,
    Html,
    Image,
    Molecule,
    Object3D,
    Text,
    Video,
    echarts,
    plot,
)
from .internal.settings import Settings
from .protocol import Callback

__all__ = [
    # cmd
    "init",
    "finish",
    "log",
    "log_text",
    "log_image",
    "log_audio",
    "log_video",
    "log_echarts",
    "log_html",
    "log_histogram",
    "log_object3d",
    "log_molecule",
    "async_log",
    "define_metric",
    "save",
    "merge_settings",
    "merge_callbacks",
    "require",
    "cmd_utils",
    # run
    "has_run",
    "get_run",
    "set_run",
    "clear_run",
    "config",
    # utils
    "pkg",
    "impl",
    # data
    "Audio",
    "ECharts",
    "Histogram",
    "Html",
    "Image",
    "Molecule",
    "Object3D",
    "Text",
    "Video",
    "echarts",
    "plot",
    # protocol
    "Callback",
    "Settings",
    "Run",
]
