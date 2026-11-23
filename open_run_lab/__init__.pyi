"""
open_run_lab public API type stubs.

This file is the single source of truth for all type signatures exposed at the
top-level `open_run_lab` namespace.  Add new public symbols here when they are added
to open_run_lab/__init__.py.
"""

from concurrent.futures import Future
from pathlib import Path
from typing import Any, Callable, List, Mapping, Optional, Sequence, Union

from . import utils
from .sdk import (
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
    config,
    echarts,
    plot,
)
from .sdk.typings.cmd import ConfigLike
from .sdk.typings.context import CallbacksType
from .sdk.typings.run import (
    AsyncLogType,
    FinishType,
    ModeType,
    ParallelType,
    ResumeType,
    SaveType,
)
from .sdk.typings.run.transforms import CaptionsType
from .sdk.typings.run.transforms.audio import AudioDatasType, AudioRatesType
from .sdk.typings.run.transforms.echarts import EChartsDatasType
from .sdk.typings.run.transforms.histogram import HistogramBins, HistogramInput
from .sdk.typings.run.transforms.html import HtmlDatasType
from .sdk.typings.run.transforms.image import ImageDatasType, ImageFilesType, ImageModesType, ImageSizesType
from .sdk.typings.run.transforms.molecule import MoleculeDatasType
from .sdk.typings.run.transforms.object3d import Object3DDatasType
from .sdk.typings.run.transforms.text import TextDatasType
from .sdk.typings.run.transforms.video import VideoDatasType

__version__: str

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
    "async_log",
    "save",
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
    "Video",
    "Object3D",
    "Molecule",
    "plot",
    "echarts",
    # utils
    "utils",
    "Settings",
    "Callback",
    # sync patches
    "sync_wandb",
    "sync_tensorboardX",
    "sync_tensorboard_torch",
    "sync_mlflow",
]

# ── lifecycle ──────────────────────────────────────────────────────────────────

def init(
    *,
    reinit: Optional[bool] = None,
    log_dir: Optional[str] = None,
    mode: Optional[ModeType] = None,
    workspace: Optional[str] = None,
    project: Optional[str] = None,
    public: Optional[bool] = None,
    name: Optional[str] = None,
    color: Optional[str] = None,
    description: Optional[str] = None,
    job_type: Optional[str] = None,
    group: Optional[str] = None,
    tags: Optional[List[str]] = None,
    id: Optional[str] = None,
    resume: Optional[Union[ResumeType, bool]] = None,
    parallel: Optional[ParallelType] = None,
    config: Optional[ConfigLike] = None,
    settings: Optional[Settings] = None,
    callbacks: Optional[CallbacksType] = None,
    **kwargs: Any,
) -> Run:
    """Initialize a new OpenRunLab run to track experiments.

    This function starts a new run for logging metrics, artifacts, and metadata.
    After calling this, use `open_run_lab.log()` to log data and `open_run_lab.finish()` to
    close the run. OpenRunLab automatically finishes runs at program exit.

    :param reinit: If True, finish the current run before starting a new one. Defaults to False.
    :param log_dir: Directory to store logs. Defaults to "./orlab-log".
    :param mode: Run mode. Options: "offline" (将数据写入本地 orlab-log 目录),
        "disabled" (no logging). Defaults to "offline".
    :param workspace: Workspace or organization name. Defaults to current user.
    :param project: Project name. Defaults to current directory name.
    :param public: 保留参数，纯本地模式下不生效。Defaults to False.
    :param name: Experiment name. Auto-generated if not provided.
    :param color: Experiment color for visualization. Auto-generated if not provided.
    :param description: Experiment description.
    :param job_type: Job type label (e.g., "train", "eval").
    :param group: Group name for organizing related experiments.
    :param tags: List of tags for categorizing experiments.
    :param id: 指定本次 run 的 id。
    :param resume: Resume behavior. Options: "must" (must resume), "allow" (resume if exists),
        "never" (always create new). Defaults to "never".
    :param parallel: Parallel execution policy. Options: "none", "shared".
    :param config: Experiment configuration dict or path to config file (JSON/YAML).
    :param settings: Custom Settings object for advanced configuration.
    :param callbacks: List of callback functions triggered on run events.

    :return: The initialized Run object.

    :raises RuntimeError: If a run is already active and reinit=False, or if startup fails.

    Examples:

        Basic local run:

        >>> import open_run_lab
        >>> open_run_lab.init(mode="offline", project="my_project")
        >>> open_run_lab.log({"loss": 0.5})
        >>> open_run_lab.finish()

        Run with configuration:

        >>> import open_run_lab
        >>> open_run_lab.init(
        ...     mode="offline",
        ...     project="image_classification",
        ...     name="resnet50_experiment",
        ...     config={"lr": 0.001, "batch_size": 32}
        ... )
        >>> open_run_lab.log({"accuracy": 0.95})
        >>> open_run_lab.finish()
    """
    ...

def finish(
    state: FinishType = "success",
    error: Optional[str] = None,
    async_log_timeout: Optional[int] = None,
) -> None:
    """Finish the current run and close the experiment.

    This function safely closes the current run and waits for all logs to be flushed.
    OpenRunLab automatically calls this function at program exit, but you can call it
    manually to mark the experiment as completed with a specific state.

    :param state: Final state of the run. Must be one of: "success", "crashed", "aborted".
        Defaults to "success".
    :param error: Error message if state is "crashed". Required when state="crashed".
    :raises RuntimeError: If called without an active run.

    Examples:

        Finish a successful run:

        >>> import open_run_lab
        >>> open_run_lab.init(mode="offline")
        >>> open_run_lab.log({"loss": 0.5})
        >>> open_run_lab.finish()

        Mark run as crashed with error message:

        >>> import open_run_lab
        >>> open_run_lab.init(mode="offline")
        >>> try:
        ...     raise ValueError("Training failed")
        ... except Exception as e:
        ...     open_run_lab.finish(state="crashed", error=str(e))
    """
    ...

def merge_settings(settings: Union[Settings, dict]) -> None:
    """Merge custom settings into the global OpenRunLab configuration.

    This function allows you to customize OpenRunLab's behavior before initializing a run.
    It must be called before `open_run_lab.init()`.

    :param settings: Custom settings to merge. Can be either a Settings object or a dict.
    :raises RuntimeError: If called while a run is active.

    Examples:

        >>> import open_run_lab
        >>> open_run_lab.merge_settings({"mode": "offline", "log_dir": "./my_logs"})
        >>> open_run_lab.init()
    """
    ...

def merge_callbacks(callbacks: CallbacksType) -> None:
    """Merge custom callbacks into the global OpenRunLab callback registry.

    This function allows you to register callbacks before initializing a run.
    It must be called before `open_run_lab.init()`.

    :param callbacks: Custom callbacks to merge. Can be a single Callback object or an iterable of Callback objects.
    :raises RuntimeError: If called while a run is active.

    Examples:

        >>> import open_run_lab
        >>> from open_run_lab import Callback
        >>> class MyCallback(Callback):
        ...     @property
        ...     def name(self) -> str:
        ...         return "my_callback"
        ...     def on_run_initialized(self, run_dir, path, *kwargs):
        ...         print("Run initialized!")
        >>> open_run_lab.merge_callbacks(MyCallback())
        >>> open_run_lab.init()
    """
    ...

def require(*requirements: str) -> List[str]:
    """Enable a transitional OpenRunLab runtime backend (process-global).

    Must be called before ``open_run_lab.init()``. Currently supported requirements:

    - ``"core"``: switch to the OpenRunLab Go core runtime (orlab-core).
    - ``"probe"``: switch to the OpenRunLab Rust probe runtime.
    - ``"core_python"``: explicitly use the built-in Python core.
    - ``"probe_python"``: explicitly use the built-in Python probe.

    Equivalent to setting the ``ORLAB_REQUIRE`` environment variable (comma-separated).
    Idempotent; unknown tokens raise ``ValueError``. This is a transitional API:
    once the new backends become the default, it will degrade to a no-op or be deprecated.

    :param requirements: One or more requirement tokens, e.g. ``"core"``, ``"probe"``.
    :return: The list of activated requirement tokens.
    :raises ValueError: If a requirement token is unknown.
    :raises RuntimeError: If called while a run is active.

    Examples:

        Switch to the Go core for a single run:

        >>> import open_run_lab
        >>> open_run_lab.require("core")
        >>> open_run_lab.init()

        Enable both core and probe via the environment variable instead:

        >>> # ORLAB_REQUIRE=core,probe python train.py
    """
    ...

# ── run access ─────────────────────────────────────────────────────────────────

run: Optional[Run]
"""The current active OpenRunLab run, or None if no run is active."""

def has_run() -> bool:
    """Check if there is an active OpenRunLab run.

    :return: True if a run is currently active, False otherwise.

    Examples:

        >>> import open_run_lab
        >>> if open_run_lab.has_run():
        ...     open_run_lab.log({"metric": 1.0})
        ... else:
        ...     print("No active run")
    """
    ...

def get_run() -> Run:
    """Get the current active OpenRunLab run.

    :return: The active Run instance.
    :raises RuntimeError: If no run is currently active.

    Examples:

        >>> import open_run_lab
        >>> open_run_lab.init(mode="offline")
        >>> run = open_run_lab.get_run()
        >>> print(run.id)
        >>> open_run_lab.finish()
    """
    ...

# ── logging ────────────────────────────────────────────────────────────────────

def log(data: Mapping[str, Any], step: Optional[int] = None) -> None:
    """Log metrics and data to the current run.

    :param data: Dictionary of metric names and values to log.
    :param step: Optional step number. If not provided, auto-increments.
    :raises RuntimeError: If called without an active run.

    Examples:

        Log multiple metrics:

        >>> import open_run_lab
        >>> open_run_lab.init(mode="offline")
        >>> open_run_lab.log({"loss": 0.5, "accuracy": 0.95})
        >>> open_run_lab.finish()

        Log with explicit step:

        >>> import open_run_lab
        >>> open_run_lab.init(mode="offline")
        >>> open_run_lab.log({"loss": 0.5}, step=10)
        >>> open_run_lab.finish()
    """
    ...

def log_text(
    *,
    key: str,
    data: TextDatasType,
    caption: CaptionsType = None,
    step: Optional[int] = None,
) -> None:
    """A syntactic sugar for logging text data.

    :param key: The key for the text data.
    :param data: The text data itself or a Text object.
    :param caption: Optional caption for the text data.
    :param step: Optional step number. If not provided, auto-increments.
    :raises RuntimeError: If called without an active run.

    Examples:

        Log simple text:

        >>> import open_run_lab
        >>> open_run_lab.init(mode="offline")
        >>> open_run_lab.log_text(key="output", data="Training started")
        >>> open_run_lab.finish()

        Log text with caption:

        >>> import open_run_lab
        >>> open_run_lab.init(mode="offline")
        >>> open_run_lab.log_text(key="prediction", data="cat", caption="Model output")
        >>> open_run_lab.finish()
    """
    ...

def log_image(
    *,
    key: str,
    data: ImageDatasType,
    mode: ImageModesType = None,
    caption: CaptionsType = None,
    file_type: ImageFilesType = None,
    size: ImageSizesType = None,
    step: Optional[int] = None,
) -> None:
    """A syntactic sugar for logging image data.

    :param key: The key for the image data.
    :param data: The image data itself or an Image object.
    :param mode: PIL mode applied when converting to PIL.Image (e.g. 'RGB', 'L').
    :param caption: Optional caption for the image data.
    :param file_type: Output file format. One of ['png', 'jpg', 'jpeg', 'bmp']. Defaults to 'png'.
    :param size: Resize policy (int for max side, (w, h) tuple for exact size).
    :param step: Optional step number. If not provided, auto-increments.
    :raises RuntimeError: If called without an active run.

    Examples:

        >>> import open_run_lab, numpy as np
        >>> open_run_lab.init(mode="offline")
        >>> img = np.zeros((64, 64, 3), dtype=np.uint8)
        >>> open_run_lab.log_image(key="sample", data=img, caption="blank image")
        >>> open_run_lab.finish()
    """
    ...

def log_audio(
    *,
    key: str,
    data: AudioDatasType,
    sample_rate: AudioRatesType = 44100,
    caption: CaptionsType = None,
    step: Optional[int] = None,
) -> None:
    """A syntactic sugar for logging audio data.

    :param key: The key for the audio data.
    :param data: The audio data itself or an Audio object.
    :param sample_rate: Sample rate of the audio (used when data is raw numpy array).
    :param caption: Optional caption for the audio data.
    :param step: Optional step number. If not provided, auto-increments.
    :raises RuntimeError: If called without an active run.

    Examples:

        >>> import open_run_lab, numpy as np
        >>> open_run_lab.init(mode="offline")
        >>> audio = np.zeros((1, 44100), dtype=np.float32)
        >>> open_run_lab.log_audio(key="sound", data=audio, sample_rate=44100)
        >>> open_run_lab.finish()
    """
    ...

def log_video(
    *,
    key: str,
    data: VideoDatasType,
    caption: CaptionsType = None,
    step: Optional[int] = None,
) -> None:
    """A syntactic sugar for logging video data.

    Currently supported formats: GIF.

    :param key: The key for the video data.
    :param data: The video data itself or a Video object.
    :param caption: Optional caption for the video data.
    :param step: Optional step number. If not provided, auto-increments.
    :raises RuntimeError: If called without an active run.

    Examples:

        >>> import open_run_lab
        >>> open_run_lab.init(mode="offline")
        >>> with open("animation.gif", "rb") as f:
        ...     open_run_lab.log_video(key="rollout", data=f.read())
        >>> open_run_lab.finish()
    """
    ...

def log_echarts(
    *,
    key: str,
    data: EChartsDatasType,
    caption: CaptionsType = None,
    step: Optional[int] = None,
) -> None:
    """A syntactic sugar for logging ECharts data.

    :param key: The key for the echarts data.
    :param data: The echarts chart object (pyecharts chart) or an ECharts object.
    :param caption: Optional caption for the echarts data.
    :param step: Optional step number. If not provided, auto-increments.
    :raises RuntimeError: If called without an active run.

    Examples:

        >>> import open_run_lab
        >>> open_run_lab.init(mode="offline")
        >>> chart = open_run_lab.echarts.Bar().add_xaxis(["a", "b"]).add_yaxis("series", [1, 2])
        >>> open_run_lab.log_echarts(key="chart", data=chart)
        >>> open_run_lab.finish()
    """
    ...

def log_html(
    *,
    key: str,
    data: HtmlDatasType,
    caption: CaptionsType = None,
    step: Optional[int] = None,
) -> None:
    """A syntactic sugar for logging HTML data.

    :param key: The key for the HTML data.
    :param data: The HTML data (raw HTML string, file path, file object, or Html object).
    :param caption: Optional caption for the HTML data.
    :param step: Optional step number. If not provided, auto-increments.
    :raises RuntimeError: If called without an active run.

    Examples:

        Log raw HTML string:

        >>> import open_run_lab
        >>> open_run_lab.init(mode="offline")
        >>> open_run_lab.log_html(key="report", data="<h1>Hello World</h1>")
        >>> open_run_lab.finish()

        Log HTML from a file path:

        >>> import open_run_lab
        >>> open_run_lab.init(mode="offline")
        >>> open_run_lab.log_html(key="page", data="./report.html", caption="My Report")
        >>> open_run_lab.finish()

        Log an Html object:

        >>> import open_run_lab
        >>> open_run_lab.init(mode="offline")
        >>> html = open_run_lab.Html("<p>Styled content</p>", caption="styled")
        >>> open_run_lab.log_html(key="styled_page", data=html)
        >>> open_run_lab.finish()
    """
    ...

def log_object3d(
    *,
    key: str,
    data: Object3DDatasType,
    caption: CaptionsType = None,
    step: Optional[int] = None,
) -> None:
    """A syntactic sugar for logging 3D object data.

    :param key: The key for the 3D object data.
    :param data: The 3D object data (numpy array, dict, file path, or Object3D object).
    :param caption: Optional caption for the 3D object data.
    :param step: Optional step number. If not provided, auto-increments.
    :raises RuntimeError: If called without an active run.

    Examples:

        >>> import open_run_lab, numpy as np
        >>> open_run_lab.init(mode="offline")
        >>> points = np.random.rand(100, 3)
        >>> open_run_lab.log_object3d(key="point_cloud", data=points, caption="random points")
        >>> open_run_lab.finish()
    """
    ...

def log_molecule(
    *,
    key: str,
    data: MoleculeDatasType,
    caption: CaptionsType = None,
    step: Optional[int] = None,
) -> None:
    """A syntactic sugar for logging molecule data.

    :param key: The key for the molecule data.
    :param data: The molecule data (SMILES string, file path, RDKit Mol object, or Molecule object).
    :param caption: Optional caption for the molecule data.
    :param step: Optional step number. If not provided, auto-increments.
    :raises RuntimeError: If called without an active run.

    Examples:

        >>> import open_run_lab
        >>> open_run_lab.init(mode="offline")
        >>> open_run_lab.log_molecule(key="molecule", data="CCO", caption="Ethanol")
        >>> open_run_lab.finish()
    """
    ...

def log_histogram(
    *,
    key: str,
    data: HistogramInput,
    bins: Optional[HistogramBins] = None,
    step: Optional[int] = None,
    **kwargs: Any,
) -> None:
    """A syntactic sugar for logging histogram data.

    :param key: The key for the histogram data.
    :param data: The histogram data (sequence, numpy array, or Histogram object).
    :param bins: Number of buckets or explicit bucket edges.
    :param num_bins: wandb-compatible bucket count, accepted via ``**kwargs``; used when bins is None.
    :param step: Optional step number. If not provided, auto-increments.
    :raises RuntimeError: If called without an active run.

    Examples:

        >>> import open_run_lab
        >>> open_run_lab.init(mode="offline")
        >>> open_run_lab.log_histogram(key="weights", data=[0.1, 0.2, 0.3], bins=16)
        >>> open_run_lab.finish()
    """
    ...

def async_log(
    func: Callable,
    *args: Any,
    step: Optional[int] = None,
    mode: AsyncLogType = "threading",
    **kwargs: Any,
) -> Future:
    """Asynchronously execute a function and automatically log its return value.

    ``func`` is submitted to a background thread, process, or the asyncio event loop
    (depending on *mode*).  When it completes, its return value — a ``dict`` — is
    passed to :func:`log` automatically.  The call returns a
    :class:`~concurrent.futures.Future` immediately.

    :func:`finish` waits for all outstanding ``async_log`` tasks before flushing,
    so no data is lost.

    :param func: A callable returning a ``dict`` suitable for :func:`log`.
    :param args: Positional arguments forwarded to *func*.
    :param step: Optional step index.  If ``None``, auto-incremented when the task
        **completes** (not when submitted).  Pass an explicit value if step ordering matters.
    :param mode: Execution mode:

        - ``"asyncio"`` — schedule on the running asyncio event loop.  *func* must be a
          coroutine (``async def``).  Raises :exc:`RuntimeError` if no loop is running.

        - ``"threading"`` (default) — background thread.  *func* can access
          ``open_run_lab.config`` and return media objects (:class:`Image`, :class:`Audio`, etc.).
          Subject to the GIL.

        - ``"spawn"`` — new child process (``mp_context=spawn``).  Bypasses the GIL, ideal
          for CPU-bound work.  *func*, its arguments, and its return value **must be
          pickle-serializable** (no :class:`Image`, ``torch.Tensor``, etc.).

        - ``"fork"`` — **reserved**.  Will be enabled after ``orlab-core`` ships.

    :param kwargs: Keyword arguments forwarded to *func*.
    :return: A :class:`~concurrent.futures.Future`.
    :raises RuntimeError: No active Run, or no asyncio event loop (``"asyncio"`` mode only).

    Examples:

        Asyncio mode — coroutine function for IO-bound work:

        >>> import open_run_lab
        >>> run = open_run_lab.init()
        >>> async def slow_compute():
        ...     import asyncio
        ...     await asyncio.sleep(2)
        ...     return {"score": 0.95}
        >>> future = open_run_lab.async_log(slow_compute, step=1, mode="asyncio")

        Threading mode (default) — IO-bound or returning media objects:

        >>> def fetch_score():
        ...     import time
        ...     time.sleep(2)
        ...     return {"score": 0.95}
        >>> future = open_run_lab.async_log(fetch_score, step=1)

        Spawn mode — CPU-bound, pickle-safe return values:

        >>> def compute_loss():
        ...     return {"loss": 0.123, "acc": 0.95}
        >>> future = open_run_lab.async_log(compute_loss, step=2, mode="spawn")
    """
    ...

def define_metric(
    key: str,
    *,
    x_axis: Optional[str] = None,
    section_name: Optional[str] = None,
    hidden: Optional[bool] = None,
    step_sync: Optional[bool] = None,
    overwrite: bool = False,
    **kwargs: Any,
) -> None:
    """Define a metric's display configuration before logging.

    Customizes how an auto-generated chart for *key* appears in project Views:
    X-axis, section placement, and visibility. The same ``(class, key)``
    shares one chart across all runs in the project.

    :param key: Metric key. Supports exact match and a single trailing ``*``
        glob (e.g. ``"train/*"``). System keys are never matched.
    :param x_axis: Custom X-axis key; ``None`` means the system step.
        ``step_metric`` is accepted as a ``**kwargs`` alias.
    :param section_name: Section name for the auto chart. ``None`` means the
        default section derived from the key.
    :param hidden: If ``True``, place the chart in the HIDDEN section.
        Three states: ``None`` (default) means "not provided" — merge mode
        keeps the previous value; ``True`` hides; ``False`` explicitly
        unhides (also effective in merge mode).
    :param step_sync: When X and Y are logged separately, whether to reuse the
        latest X value on the current step. Defaults to ``True`` when
        ``x_axis`` (or ``step_metric``) is set, ``False`` otherwise.
    :param overwrite: If ``False`` (default), merge with previous calls for
        the same ``key``. If ``True``, unspecified fields reset to default.

    .. note::
        Project-wide first-writer-wins: the chart for ``(class, key)`` is
        shared across all runs, and ``define_metric`` only takes effect on
        the first run that introduces the key to the project. Once the chart
        exists, later calls (including ``overwrite=True``) have no effect.

    Examples:

        Custom X-axis with separate logging:

        >>> import open_run_lab
        >>> open_run_lab.init(mode="offline")
        >>> run = open_run_lab.get_run()
        >>> run.define_metric("train/loss", x_axis="train/epoch")
        >>> open_run_lab.log({"train/epoch": 1})    # step=1
        >>> open_run_lab.log({"train/loss": 0.8})   # step=2, auto-syncs train/epoch=1

        Glob pattern for all validation metrics:

        >>> run.define_metric("val/*", section_name="Validation")
    """
    ...

def save(
    glob_str: Union[str, bytes],
    base_path: Optional[Union[str, Path]] = None,
    policy: SaveType = "live",
) -> List[str]:
    """Save files matched by glob into the current run.

    :param glob_str: A glob pattern matching files to save (e.g. ``"checkpoints/*.pt"``).
    :param base_path: Base directory for resolving relative paths. Defaults to cwd.
    :param policy: Save policy:

        - ``"now"`` — upload matched files immediately.
        - ``"end"`` — defer upload until the run finishes.
        - ``"live"`` — watch for file changes and re-upload automatically.
          Unavailable with ``core.skip_store=True``: downgraded to ``"now"``
          with a warning, so later file changes are not uploaded.

    :return: List of matched file paths (relative to base_path).
    """
    ...

# ── sync patches ────────────────────────────────────────────────────────────────

def sync_wandb(
    mode: ModeType = "offline",
    wandb_run: bool = True,
    workspace: Optional[str] = None,
    log_dir: Optional[str] = None,
) -> None:
    """Monkey-patch wandb to mirror all logged data into OpenRunLab in real time.

    Call this **before** ``wandb.init()``.  Once active, every call to
    ``wandb.init``, ``wandb.log``, ``wandb.config.update``, and ``wandb.finish``
    is forwarded to the corresponding OpenRunLab API.  The original wandb behaviour
    is preserved — data is sent to both backends simultaneously.

    :param mode: OpenRunLab run mode — ``"offline"`` | ``"disabled"``.
    :param wandb_run: If ``False``, wandb is forced into offline mode so it does
        not upload to its own cloud.  OpenRunLab still receives the data. Defaults to ``True``.
    :param workspace: OpenRunLab workspace (organization) name. Defaults to the current user.
    :param log_dir: Local directory for OpenRunLab log files.
    :raises ImportError: If ``wandb`` is not installed.

    Examples::

        Mirror wandb logs to OpenRunLab Cloud:

        >>> import open_run_lab
        >>> open_run_lab.sync_wandb()
        >>> import wandb
        >>> wandb.init(project="demo", config={"lr": 0.01})
        >>> wandb.log({"loss": 0.5})
        >>> wandb.finish()

        Disable wandb cloud upload while still recording in OpenRunLab:

        >>> import open_run_lab
        >>> open_run_lab.sync_wandb(wandb_run=False)
        >>> import wandb
        >>> wandb.init(project="demo")
        >>> wandb.log({"loss": 0.5})
        >>> wandb.finish()
    """
    ...

def sync_tensorboardX(types: Optional[Sequence[str]] = None) -> None:
    """Monkey-patch tensorboardX SummaryWriter to mirror logs to OpenRunLab.

    Call this **before** creating a ``SummaryWriter`` instance.  Once active,
    calls to ``add_scalar``, ``add_scalars``, ``add_image``, ``add_text``,
    ``__init__``, and ``close`` are forwarded to the corresponding OpenRunLab API.

    :param types: Data types to sync. Options: ``"scalar"``, ``"scalars"``,
        ``"image"``, ``"text"``.  ``None`` syncs all types.
    :raises ImportError: If ``tensorboardX`` is not installed.

    Examples::

        Sync all data types:

        >>> import open_run_lab
        >>> open_run_lab.sync_tensorboardX()
        >>> from tensorboardX import SummaryWriter
        >>> writer = SummaryWriter("runs/example")
        >>> writer.add_scalar("loss", 0.5, 0)
        >>> writer.close()

        Sync only scalars:

        >>> import open_run_lab
        >>> open_run_lab.sync_tensorboardX(types=["scalar", "scalars"])
    """
    ...

def sync_tensorboard_torch(types: Optional[Sequence[str]] = None) -> None:
    """Monkey-patch ``torch.utils.tensorboard.SummaryWriter`` to mirror logs to OpenRunLab.

    Call this **before** creating a ``SummaryWriter`` instance.  Once active,
    calls to ``add_scalar``, ``add_scalars``, ``add_image``, ``add_text``,
    ``__init__``, and ``close`` are forwarded to the corresponding OpenRunLab API.

    :param types: Data types to sync. Options: ``"scalar"``, ``"scalars"``,
        ``"image"``, ``"text"``.  ``None`` syncs all types.
    :raises ImportError: If ``torch`` is not installed.

    Examples::

        >>> import open_run_lab
        >>> open_run_lab.sync_tensorboard_torch()
        >>> from torch.utils.tensorboard import SummaryWriter
        >>> writer = SummaryWriter("runs/example")
        >>> writer.add_scalar("loss", 0.5, 0)
        >>> writer.close()
    """
    ...

def sync_mlflow(mode: ModeType = "offline") -> None:
    """Monkey-patch mlflow to forward logs to OpenRunLab.

    Call before any mlflow API usage. Intercepts ``mlflow.set_experiment``,
    ``mlflow.start_run``, ``mlflow.end_run``, ``mlflow.log_param(s)``,
    ``mlflow.log_metric(s)`` and mirrors the data into OpenRunLab.

    Args:
        mode: OpenRunLab run mode. Defaults to ``"offline"``.

    Example::

        >>> import open_run_lab
        >>> open_run_lab.sync_mlflow()
        >>>
        >>> import mlflow
        >>> mlflow.set_experiment("my_experiment")
        >>> with mlflow.start_run(run_name="my_run"):
        ...     mlflow.log_param("lr", 0.01)
        ...     mlflow.log_metric("loss", 0.5, step=0)
    """
    ...
