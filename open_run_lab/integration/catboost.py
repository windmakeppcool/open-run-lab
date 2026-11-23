from __future__ import annotations

from typing import TYPE_CHECKING

import open_run_lab
from open_run_lab import Callback

if TYPE_CHECKING:
    from typing import Any, Dict, List, NamedTuple, Optional

    class IterationInfo(NamedTuple):
        iteration: int
        metrics: Dict[str, Dict[str, List[float]]]


class OpenRunLabCallback(Callback):
    def __init__(self, params: Optional[Dict[str, Any]] = None):
        self._params = params
        self._initialized = False

    @property
    def name(self) -> str:
        return "orlab-integration-catboost"

    def _init(self) -> None:
        if self._initialized:
            return
        run = open_run_lab.get_run()
        if run is None:
            return
        self._initialized = True
        run.config["FRAMEWORK"] = "catboost"
        if self._params and isinstance(self._params, dict):
            run.config.update(self._params)

    def after_iteration(self, info: IterationInfo) -> bool:
        self._init()
        if not info.metrics:
            return True

        for stage_name, metrics in info.metrics.items():
            for metric_name, values in metrics.items():
                if values:
                    open_run_lab.log({f"{stage_name}_{metric_name}": values[-1]}, step=info.iteration)

        return True
