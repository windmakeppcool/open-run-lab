from __future__ import annotations

from typing import Any, Optional

import open_run_lab
import open_run_lab.vendor
from open_run_lab import Callback

_on_main_process = open_run_lab.vendor.accelerate.tracking.on_main_process
_GeneralTracker = open_run_lab.vendor.accelerate.tracking.GeneralTracker


class OpenRunLabTracker(Callback, _GeneralTracker):
    requires_logging_directory = False
    main_process_only = True

    def __init__(
        self,
        *,
        project: Optional[str] = None,
        workspace: Optional[str] = None,
        experiment_name: Optional[str] = None,
        description: Optional[str] = None,
        log_dir: Optional[str] = None,
        logdir: Optional[str] = None,
        mode: Optional[str] = None,
        **kwargs: Any,
    ) -> None:
        if logdir is not None:
            import warnings

            warnings.warn(
                "The `logdir` parameter is deprecated, use `log_dir` instead.", DeprecationWarning, stacklevel=2
            )
            log_dir = logdir
        self._init_kwargs: dict[str, Any] = {}
        for key, value in [
            ("project", project),
            ("workspace", workspace),
            ("experiment_name", experiment_name),
            ("description", description),
            ("log_dir", log_dir),
            ("mode", mode),
        ]:
            if value is not None:
                self._init_kwargs[key] = value
        self._init_kwargs.update(kwargs)
        self._initialized = False

    @property
    def name(self) -> str:
        return "orlab"

    @property
    def tracker(self):
        return self._get_active_run() or self

    # --- open_run_lab.Callback hooks ---

    def on_run_initialized(self, run_dir, path, **kwargs) -> None:
        run = self._get_active_run()
        if run is not None:
            run.config["FRAMEWORK"] = "accelerate"
        self._initialized = True

    def on_run_finished(self, state: str, error: Optional[str] = None) -> None:
        self._initialized = False

    # --- accelerate.GeneralTracker interface ---

    @_on_main_process
    def store_init_configuration(self, values: dict) -> None:
        self._ensure_init()
        run = self._get_active_run()
        if run is not None:
            run.config.update(values)

    @_on_main_process
    def log(self, values: dict, step: Optional[int] = None, **kwargs) -> None:
        self._ensure_init()
        open_run_lab.log(values, step=step, **kwargs)

    @_on_main_process
    def finish(self) -> None:
        pass

    # --- helpers ---

    def _ensure_init(self) -> None:
        if self._initialized:
            return
        if self._get_active_run() is not None:
            self._initialized = True
            return
        open_run_lab.init(callbacks=[self], **self._init_kwargs)

    @staticmethod
    def _get_active_run():
        try:
            return open_run_lab.get_run()
        except RuntimeError:
            return None
