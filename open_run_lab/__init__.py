from open_run_lab.converter.mlf.sync import sync_mlflow
from open_run_lab.converter.tfb.sync import sync_tensorboard_torch, sync_tensorboardX
from open_run_lab.converter.wb.sync import sync_wandb
from open_run_lab.sdk import (
    Audio,
    Callback,
    ECharts,
    Histogram,
    Html,
    Image,
    Molecule,
    Object3D,
    Run,
    Settings,
    Text,
    Video,
    async_log,
    config,
    define_metric,
    echarts,
    finish,
    get_run,
    has_run,
    init,
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
    merge_callbacks,
    merge_settings,
    pkg,
    plot,
    require,
    save,
)

from . import utils
from .deprecated.callbacks import register_callbacks
from .deprecated.echarts import confusion_matrix, pr_curve, roc_curve

__version__ = pkg.helper.get_orlab_version()

__all__ = [
    # cmd
    "merge_callbacks",
    "merge_settings",
    "require",
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
    "define_metric",
    "save",
    "async_log",
    # run
    "run",  # type: ignore [no-redef]
    "Run",
    "has_run",
    "get_run",
    # config
    "config",
    # data
    "Text",
    "Audio",
    "ECharts",
    "Histogram",
    "Html",
    "Image",
    "Molecule",
    "Object3D",
    "Video",
    "plot",
    "echarts",
    # utils
    "utils",
    "Settings",
    "Callback",
    # deprecated
    "roc_curve",
    "pr_curve",
    "confusion_matrix",
    "register_callbacks",
    # sync patches
    "sync_wandb",
    "sync_tensorboardX",
    "sync_tensorboard_torch",
    "sync_mlflow",
]


def __getattr__(name: str):
    if name == "run":
        try:
            return get_run()
        except RuntimeError:
            return None
    raise AttributeError(f"module 'open_run_lab' has no attribute {name!r}")
