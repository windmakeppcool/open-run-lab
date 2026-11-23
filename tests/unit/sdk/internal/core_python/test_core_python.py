"""
@author: cunyue
@file: test_core_python.py
@time: 2026/4/19
@description: CorePython 单元测试（纯本地版本）

测试分组：
  - TestCorePythonStart  : offline / disabled 模式 deliver_run_start 行为
  - TestCorePythonPublish: offline 模式数据落盘行为
  - TestCorePythonFinish : offline 模式 deliver_run_finish 行为
  - TestCorePythonGuard  : 防御逻辑
"""

from unittest.mock import patch

import pytest

from open_run_lab.proto.orlab.grpc.core.v1.core_pb2 import (
    DeliverRunFinishRequest,
    DeliverRunStartRequest,
)
from open_run_lab.proto.orlab.run.v1.run_pb2 import FinishRecord, RunState, StartRecord
from open_run_lab.proto.orlab.settings.core.v1.core_pb2 import CoreSettings as CoreSettingsPb
from open_run_lab.sdk.internal.core_python import CorePython
from open_run_lab.sdk.internal.core_python.store import DataStoreWriter, NullDataStoreWriter


def _start_request(tmp_path, *, skip_store: bool = False) -> DeliverRunStartRequest:
    run_dir = tmp_path / "run"
    run_dir.mkdir(parents=True, exist_ok=True)
    return DeliverRunStartRequest(
        core_settings=CoreSettingsPb(
            run_id="test-run-id",
            run_dir=str(run_dir),
            section_rule=0,
            record_batch=10000,
            record_interval=5.0,
            save_split=100 * 1024 * 1024,
            save_size=50 * 1024 * 1024 * 1024,
            save_part=32 * 1024 * 1024,
            save_batch=100,
            skip_store=skip_store,
        ),
        start_record=StartRecord(id="test-run-id", project="test-project"),
    )


class TestCorePythonStart:
    def test_offline_start_success(self, tmp_path):
        core = CorePython("offline")
        resp = core.deliver_run_start(_start_request(tmp_path))

        assert resp.success is True
        assert isinstance(core._store, DataStoreWriter)
        assert core._metrics is not None
        assert core._ctx.run_file.exists()

    def test_disabled_start_does_not_init_store(self, tmp_path):
        core = CorePython("disabled")
        resp = core.deliver_run_start(_start_request(tmp_path))

        assert resp.success is True
        assert core._store is None
        assert core._metrics is None

    def test_skip_store_uses_null_writer(self, tmp_path):
        core = CorePython("offline")
        resp = core.deliver_run_start(_start_request(tmp_path, skip_store=True))

        assert resp.success is True
        assert isinstance(core._store, NullDataStoreWriter)
        assert not core._ctx.run_file.exists()


class TestCorePythonPublish:
    def test_offline_upsert_before_start_is_ignored(self, tmp_path):
        """未启动时 upsert 只告警，不抛错"""
        core = CorePython("offline")
        with patch("open_run_lab.sdk.internal.core_python.core.console.warning") as warning:
            core.upsert_scalars([])
        warning.assert_called_once()

    def test_offline_upsert_columns_persists(self, tmp_path):
        from open_run_lab.proto.orlab.metric.column.v1.column_pb2 import (
            ColumnClass,
            ColumnRecord,
            ColumnType,
        )

        core = CorePython("offline")
        core.deliver_run_start(_start_request(tmp_path))
        column = ColumnRecord(
            column_key="loss",
            column_name="loss",
            column_class=ColumnClass.COLUMN_CLASS_CUSTOM,
            column_type=ColumnType.COLUMN_TYPE_SCALAR,
        )
        core.upsert_columns([column])

        assert core._metrics.get("loss") is not None


class TestCorePythonFinish:
    def test_offline_finish_releases_store(self, tmp_path):
        core = CorePython("offline")
        core.deliver_run_start(_start_request(tmp_path))
        resp = core.deliver_run_finish(
            DeliverRunFinishRequest(finish_record=FinishRecord(state=RunState.RUN_STATE_FINISHED))
        )

        assert resp.success is True
        assert core._store is None

    def test_finish_before_start_returns_failure(self):
        core = CorePython("offline")
        resp = core.deliver_run_finish(
            DeliverRunFinishRequest(finish_record=FinishRecord(state=RunState.RUN_STATE_FINISHED))
        )

        assert resp.success is False


class TestCorePythonGuard:
    def test_error_state_writes_error_log_record(self, tmp_path):
        core = CorePython("offline")
        core.deliver_run_start(_start_request(tmp_path))
        resp = core.deliver_run_finish(
            DeliverRunFinishRequest(finish_record=FinishRecord(state=RunState.RUN_STATE_CRASHED, error="boom"))
        )

        assert resp.success is True
        assert core._ctx.run_file.exists()

    def test_fork_raises(self):
        core = CorePython("offline")
        with pytest.raises(RuntimeError, match="fork"):
            core.fork()

    def test_confirm_finish_when_not_active(self):
        core = CorePython("offline")
        resp = core.confirm_run_finish()
        assert resp.success is True
