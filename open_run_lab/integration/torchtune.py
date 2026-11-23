"""
Docs: https://docs.orlab.cn/guide_cloud/integration/integration-pytorch-torchtune.html

Usage:
------
# In torchtune config:
metric_logger:
    _component_: open_run_lab.integration.torchtune.OpenRunLabLogger
    project: "gemma-lora-finetune"
    experiment_name: "gemma-2b"
    log_dir: ${output_dir}

# Or programmatically:
from open_run_lab.integration.torchtune import OpenRunLabLogger

logger = OpenRunLabLogger(project="my-project")
# logger.log("loss", 0.5, step=100)
# logger.close()
------
"""

from __future__ import annotations

from typing import Any, Dict, List, Mapping, Optional, Union

import open_run_lab
import open_run_lab.vendor

_MetricLoggerInterface = open_run_lab.vendor.torchtune.utils.metric_logging.MetricLoggerInterface
_get_world_size_and_rank = open_run_lab.vendor.torchtune.utils._distributed.get_world_size_and_rank

Scalar = Union[Any, int, float]


class OpenRunLabLogger(_MetricLoggerInterface):
    """
    TorchTune metric logger implementing ``torchtune.utils.metric_logging.MetricLoggerInterface``.

    This logger internally calls ``open_run_lab.init()`` on construction (rank 0 only)
    and ``open_run_lab.finish()`` on ``close()`` / ``__del__`` for backward compatibility
    with torchtune's lifecycle.

    Example:
        In torchtune config:
        >>> metric_logger:
        >>>     _component_: open_run_lab.integration.torchtune.OpenRunLabLogger
        >>>     project: "gemma-lora-finetune"
        >>>     experiment_name: "gemma-2b"
        >>>     log_dir: ${output_dir}
    """

    def __init__(
        self,
        project: str = "torchtune",
        workspace: Optional[str] = None,
        experiment_name: Optional[str] = None,
        description: Optional[str] = None,
        mode: Optional[str] = None,
        log_dir: Optional[str] = None,
        logdir: Optional[str] = None,
        tags: Optional[List[str]] = None,
        **kwargs: Any,
    ) -> None:
        if logdir is not None:
            import warnings

            warnings.warn(
                "The `logdir` parameter is deprecated, use `log_dir` instead.", DeprecationWarning, stacklevel=2
            )
            log_dir = logdir

        # Use dir if specified, otherwise use log_dir.
        self.log_dir = kwargs.pop("dir", log_dir)

        tags = list(tags) if tags else []
        if "torchtune" not in tags:
            tags.append("torchtune")

        _, self.rank = _get_world_size_and_rank()

        if self.rank == 0:
            init_kwargs: Dict[str, Any] = {
                "project": project,
                "workspace": workspace,
                "name": experiment_name,
                "description": description,
                "mode": mode,
                "logdir": self.log_dir,
                "tags": tags,
            }
            init_kwargs.update(kwargs)
            # Remove None values so open_run_lab.init uses defaults
            init_kwargs = {k: v for k, v in init_kwargs.items() if v is not None}
            open_run_lab.init(**init_kwargs)
            open_run_lab.config["FRAMEWORK"] = "torchtune"

        self.config_allow_val_change = kwargs.get("allow_val_change", False)

    def update_config(self, config: Dict[str, Any]) -> None:
        if self.rank == 0:
            open_run_lab.config.update(config)

    def log_config(self, config: Any) -> None:
        if self.rank != 0:
            return
        run = _get_active_run()
        if run is None:
            return
        resolved = _resolve_config(config)
        if resolved is not None:
            run.config.update(resolved, allow_val_change=self.config_allow_val_change)

    def log(self, name: str, data: Scalar, step: int) -> None:
        if self.rank == 0:
            open_run_lab.log({name: data}, step=step)

    def log_dict(self, payload: Mapping[str, Scalar], step: int) -> None:
        if self.rank == 0:
            open_run_lab.log(dict(payload), step=step)

    def close(self) -> None:
        if self.rank == 0:
            run = _get_active_run()
            if run is not None:
                open_run_lab.finish()


# --- helpers ---


def _get_active_run():
    try:
        return open_run_lab.get_run()
    except RuntimeError:
        return None


def _resolve_config(config: Any) -> Optional[Dict[str, Any]]:
    """Resolve OmegaConf DictConfig or plain dict to a plain dict."""
    if config is None:
        return None
    if isinstance(config, dict):
        return dict(config)
    # Handle OmegaConf DictConfig
    to_container = getattr(config, "to_container", None)
    if callable(to_container):
        try:
            resolved = to_container(config, resolve=True)
            if isinstance(resolved, dict):
                return dict(resolved)
        except Exception:
            pass
    # Fallback: try omegaconf.OmegaConf.to_container
    try:
        import omegaconf

        resolved = omegaconf.OmegaConf.to_container(config, resolve=True)
        if isinstance(resolved, dict):
            return {str(k): v for k, v in resolved.items()}
    except Exception:
        pass
    return None


__all__ = ["OpenRunLabLogger"]
