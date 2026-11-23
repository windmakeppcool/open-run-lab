from concurrent.futures import thread as futures_thread
from pathlib import Path
from types import SimpleNamespace
from typing import cast
from unittest.mock import MagicMock

from open_run_lab.sdk.internal.pkg import console
from open_run_lab.sdk.internal.probe_python.context import ProbeConfig, ProbeContext
from open_run_lab.sdk.internal.probe_python.monitor import Monitor
from open_run_lab.sdk.internal.probe_python.protocol import CollectorProtocol
from open_run_lab.sdk.internal.probe_python.typings import SystemScalar, SystemShim
from open_run_lab.sdk.protocol import CoreProtocol


class _Collector(CollectorProtocol):
    def collect(self):
        return [("cpu.util", 0.5)]


def test_monitor_collects_without_executor_error_during_interpreter_shutdown(monkeypatch, tmp_path):
    shim = SystemShim(slug="linux", enable_cpu=True)
    collector = _Collector(shim)
    scalar = SystemScalar(key="cpu.util", chart_name="CPU")
    upsert_scalars = MagicMock()
    core = cast(CoreProtocol, SimpleNamespace(upsert_columns=MagicMock(), upsert_scalars=upsert_scalars))
    ctx = ProbeContext(
        config=ProbeConfig(
            run_id="run-id",
            run_dir=tmp_path,
            global_system_step=0,
            hardware=True,
            runtime=False,
            requirements=False,
            conda=False,
            git=False,
            orlab=False,
            monitor=True,
            monitor_interval=3600,
            monitor_disk_dir=Path(tmp_path),
        )
    )

    monkeypatch.setattr("open_run_lab.sdk.internal.probe_python.monitor.CPU.new", lambda _shim: (collector, [scalar]))
    monkeypatch.setattr("open_run_lab.sdk.internal.probe_python.monitor.Memory.new", lambda _shim: None)
    monkeypatch.setattr("open_run_lab.sdk.internal.probe_python.monitor.Apple.new", lambda _shim: None)
    monkeypatch.setattr("open_run_lab.sdk.internal.pkg.timer.Timer.start", lambda self: self)

    trace_mock = MagicMock()
    monkeypatch.setattr(console, "trace", trace_mock)

    monitor = Monitor(shim, core).start(ctx)
    assert monitor is not None

    monkeypatch.setattr(futures_thread, "_shutdown", True)
    monitor._timer._execute_once()  # type: ignore[union-attr]
    monkeypatch.setattr(futures_thread, "_shutdown", False)
    monitor.stop()

    trace_mock.assert_not_called()
    upsert_scalars.assert_called_once()
