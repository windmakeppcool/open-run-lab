"""
@author: cunyue
@description: 部分即将弃用的echarts语法糖
"""

import warnings

from typing_extensions import deprecated

from open_run_lab.sdk.internal.run.transforms import echarts


@deprecated(
    "`open_run_lab.roc_curve()` is deprecated and will be removed in v0.11, use `open_run_lab.echarts.roc_curve()` instead."
)
def roc_curve(*args, **kwargs):
    warnings.warn(
        "`open_run_lab.roc_curve()` is deprecated and will be removed in v0.11, use `open_run_lab.echarts.roc_curve()` instead",
        FutureWarning,
        stacklevel=2,
    )
    return echarts.roc_curve(*args, **kwargs)


@deprecated(
    "`open_run_lab.pr_curve()` is deprecated and will be removed in v0.11, use `open_run_lab.echarts.pr_curve()` instead."
)
def pr_curve(*args, **kwargs):
    warnings.warn(
        "`open_run_lab.pr_curve()` is deprecated and will be removed in v0.11, use `open_run_lab.echarts.pr_curve()` instead",
        FutureWarning,
        stacklevel=2,
    )
    return echarts.pr_curve(*args, **kwargs)


@deprecated(
    "`open_run_lab.confusion_matrix()` is deprecated and will be removed in v0.11, "
    "use `open_run_lab.echarts.confusion_matrix()` instead."
)
def confusion_matrix(*args, **kwargs):
    warnings.warn(
        "`open_run_lab.confusion_matrix()` is deprecated and will be removed in v0.11, "
        "use `open_run_lab.echarts.confusion_matrix()` instead",
        FutureWarning,
        stacklevel=2,
    )
    return echarts.confusion_matrix(*args, **kwargs)
