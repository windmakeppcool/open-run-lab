"""
@author: cunyue
@file: core.py
@time: 2026/5/14 14:21
@description: core 协议实现，OpenRunLab Core Python 版本，纯本地数据持久化实现，包括：
1. 将指标/日志/文件记录写入本地 orlab-log 存储。
2. 提供指标上下文，便于分布式训练时的指标同步。

实现 CoreProtocol，当前为纯 Python 实现。
未来由 orlab-core（Go 二进制）替代时，此模块整体被替换，
BackgroundConsumer 等调用方无需修改。

Core 需要根据不同模式处理不同的业务，这是设计模式决定的
值得说明的是，在当前的上层设计中，upsert 方法在 disabled 模式下永远不会触发，但是考虑到设计完整性，我们增加了相关业务逻辑判断
"""

from typing import List, Optional

from open_run_lab.proto.orlab.grpc.core.v1.core_pb2 import (
    ConfirmRunFinishResponse,
    DeliverRunFinishRequest,
    DeliverRunFinishResponse,
    DeliverRunStartRequest,
    DeliverRunStartResponse,
)
from open_run_lab.proto.orlab.metric.column.v1.column_pb2 import ColumnClass, ColumnRecord, ColumnType
from open_run_lab.proto.orlab.metric.data.v1.data_pb2 import HistogramRecord, MediaRecord, ScalarRecord
from open_run_lab.proto.orlab.record.v1.record_pb2 import Record
from open_run_lab.proto.orlab.run.v1.run_pb2 import FinishRecord, RunState
from open_run_lab.proto.orlab.save.v1.save_pb2 import SaveRecord, SaveType
from open_run_lab.proto.orlab.terminal.v1.log_pb2 import LogLevel, LogRecord
from open_run_lab.sdk.internal.core_python.context import CoreContext
from open_run_lab.sdk.internal.core_python.metrics import RunMetrics
from open_run_lab.sdk.internal.core_python.pkg import builder, counter
from open_run_lab.sdk.internal.core_python.store import DataStoreWriter, DataStoreWriterProtocol, NullDataStoreWriter
from open_run_lab.sdk.internal.core_python.watcher import (
    FileWatcher,
    FileWatcherProtocol,
    NullFileWatcher,
    create_save_links,
)
from open_run_lab.sdk.internal.pkg import adapter, console, safe
from open_run_lab.sdk.protocol import CoreProtocol
from open_run_lab.sdk.typings.run import ModeType

__all__ = ["CorePython"]


class CorePython(CoreProtocol):
    """
    CoreProtocol 的 Python 实现。
    由 Run 在初始化时构造并注入给 BackgroundConsumer
    """

    def __init__(self, mode: ModeType):
        super().__init__(mode)
        self._run_ctx: Optional[CoreContext] = None
        self._store: Optional[DataStoreWriterProtocol] = None
        # 标记core是否激活，未激活时拒绝接受上报数据，表达一个完整的生命周期状态：
        # initialized but not started -> active -> finished
        self._active = False
        # record 构建计数器
        self._counter = counter.Counter()
        # console 行计数器
        self._epoch = counter.Counter()
        # 指标上下文管理器
        self._metrics: Optional[RunMetrics] = None
        # save 相关
        self._watcher: Optional[FileWatcherProtocol] = None

    @property
    def _ctx(self) -> CoreContext:
        assert self._run_ctx, "run context not set"
        return self._run_ctx

    @_ctx.setter
    def _ctx(self, ctx: CoreContext):
        self._run_ctx = ctx

    # ---------------------------------- 实验开始 ----------------------------------

    def deliver_run_start(self, start_request: DeliverRunStartRequest) -> DeliverRunStartResponse:
        if self._active:
            return DeliverRunStartResponse(success=False, message="Run has already been active.")
        resp = super().deliver_run_start(start_request)
        # 启动失败统一在这里清理，与具体的模式实现解耦
        if not resp.success:
            self._cleanup_failed_start()
        self._active = resp.success
        return resp

    def _start_store(self, resp: DeliverRunStartResponse):
        # skip_store 模式下使用空写入器与空监听器，跳过本地存储和文件监听
        if self._ctx.config.skip_store:
            self._store = NullDataStoreWriter()
            self._watcher = NullFileWatcher()
        else:
            self._store = DataStoreWriter()
            self._watcher = FileWatcher(on_change=self._on_file_changed)
        self._store.open(str(self._ctx.run_file))
        self._store_records([builder.build_start_record(resp.run)])

    def _start_when_offline(self, start_request: DeliverRunStartRequest) -> DeliverRunStartResponse:
        self._ctx = CoreContext.from_proto(start_request.core_settings)
        self._metrics, console_epoch, global_step, global_system_step = RunMetrics.new(None, ctx=self._ctx)
        resp = DeliverRunStartResponse(
            success=True,
            message="OK, but use offline",
            run=start_request.start_record,
            new_experiment=True,
            global_system_step=global_system_step,
            global_step=global_step,
        )
        self._epoch.reset(console_epoch)
        self._start_store(resp)
        return resp

    def _cleanup_failed_start(self) -> None:
        """启动失败后由 Core 自行释放已创建的资源，不删除 run file。"""
        self._metrics = None
        with safe.block(message="Failed to release local storage after start failure"):
            self._release_local_storage()
        self._run_ctx = None

    # ---------------------------------- 数据上报 ----------------------------------

    def _store_records(self, records: List[Record]) -> None:
        """将一组 Record 写入本地存储。"""
        assert self._store is not None, "store must be initialized before upsert"
        if self._ctx.config.skip_store:
            # skip_store：跳过本地序列化与写入
            return
        for record in records:
            self._store.write(record.SerializeToString())

    # ---- upsert_columns ----

    def upsert_columns(self, columns: List[ColumnRecord]) -> None:
        if not self._active:
            console.warning("Core is not active, refusing to upsert columns")
            return
        return super().upsert_columns(columns)

    def _upsert_columns_to_metrics(self, columns: List[ColumnRecord]):
        assert self._metrics is not None, "metrics must be initialized before upsert columns"
        records: List[Record] = []
        for column in columns:
            # 1. 已存在则跳过
            if self._metrics.get(column.column_key):
                handle = console.debug if column.column_class == ColumnClass.COLUMN_CLASS_SYSTEM else console.warning
                handle(f"Column {column.column_key} already has been defined, skipping")
                continue
            # 2. 否则定义指标，根据类型不同，定义不同的指标
            if column.column_type == ColumnType.COLUMN_TYPE_SCALAR:
                self._metrics.define_scalar(key=column.column_key, column=column)
            elif column.column_type == ColumnType.COLUMN_TYPE_HISTOGRAM:
                self._metrics.define_histogram(key=column.column_key, column=column)
            else:
                self._metrics.define_media(
                    key=column.column_key, column=column, path=adapter.medium[column.column_type]
                )
            records.append(builder.build_column_record(self._counter, column))
        self._store_records(records)
        return records

    def _upsert_columns_when_offline(self, columns: List[ColumnRecord]) -> None:
        self._upsert_columns_to_metrics(columns)

    # ---- upsert_scalars ----

    def upsert_scalars(self, scalars: List[ScalarRecord]) -> None:
        if not self._active:
            console.warning("Core is not active, refusing to upsert scalars")
            return
        return super().upsert_scalars(scalars)

    def _upsert_scalars_to_metrics(self, scalars_list: List[ScalarRecord]) -> List[Record]:
        """
        将一组 ScalarRecord 转换为一组 Record，并更新指标上下文
        """
        assert self._metrics is not None, "metrics must be initialized before upsert scalars"
        records: List[Record] = []
        for scalar in scalars_list:
            with safe.block(message="Failed to upsert scalar metric ctx"):
                # 1. 如果指标未定义，则定义此指标
                metric = self._metrics.get(scalar.key)
                if not metric:
                    column_record = builder.build_auto_column(self._ctx, scalar)
                    metric = self._metrics.define_scalar(key=scalar.key, column=column_record)
                    records.append(builder.build_column_record(self._counter, column_record))
                # 2. 检查类型是否匹配，判断指定的step是否允许写入
                metric.ensure_type_match(scalar.type)
                if metric.try_accept_step(scalar.step):
                    metric.update(scalar)
                    records.append(builder.build_scalar_record(self._counter, scalar))
                else:
                    console.debug(
                        f"Metric '{scalar.key}' at step {scalar.step} was skipped because it is duplicate or too old."
                    )
        # 持久化存储record
        self._store_records(records)
        return records

    def _upsert_scalars_when_offline(self, scalars: List[ScalarRecord]) -> None:
        self._upsert_scalars_to_metrics(scalars)

    # ---- upsert_media -----

    def upsert_media(self, media: List[MediaRecord]) -> None:
        if not self._active:
            console.warning("Core is not active, refusing to upsert media")
            return
        return super().upsert_media(media)

    def _upsert_media_to_metrics(self, media_list: List[MediaRecord]) -> List[Record]:
        assert self._metrics is not None, "metrics must be initialized before upsert media"
        records: List[Record] = []
        for media in media_list:
            with safe.block(message="Failed to upsert media metric ctx"):
                # 1. 如果指标未定义，则定义此指标
                metric = self._metrics.get(media.key)
                if not metric:
                    column_record = builder.build_auto_column(self._ctx, media)
                    metric = self._metrics.define_media(
                        key=media.key, column=column_record, path=self._ctx.media_dir / adapter.medium[media.type]
                    )
                    records.append(builder.build_column_record(self._counter, column_record))
                # 2. 检查类型是否匹配，判断指定的step是否允许写入
                metric.ensure_type_match(media.type)
                if metric.try_accept_step(media.step):
                    metric.update(media)
                    records.append(builder.build_media_record(self._counter, media))
                else:
                    console.debug(
                        f"Metric '{media.key}' at step {media.step} was skipped because it is duplicate or too old."
                    )
            # 持久化存储record
        self._store_records(records)
        return records

    def _upsert_media_when_offline(self, media: List[MediaRecord]) -> None:
        self._upsert_media_to_metrics(media)

    # ---- upsert_histograms ----

    def upsert_histograms(self, histograms: List[HistogramRecord]) -> None:
        if not self._active:
            console.warning("Core is not active, refusing to upsert histograms")
            return
        return super().upsert_histograms(histograms)

    def _upsert_histograms_to_metrics(self, histograms: List[HistogramRecord]) -> List[Record]:
        """
        将一组 HistogramRecord 转换为一组 Record，并更新指标上下文
        """
        assert self._metrics is not None, "metrics must be initialized before upsert histograms"
        records: List[Record] = []
        for histogram in histograms:
            with safe.block(message="Failed to upsert histogram metric ctx"):
                # 1. 如果指标未定义，则定义此指标
                metric = self._metrics.get(histogram.key)
                if not metric:
                    column_record = builder.build_auto_column(self._ctx, histogram)
                    metric = self._metrics.define_histogram(key=histogram.key, column=column_record)
                    records.append(builder.build_column_record(self._counter, column_record))
                # 2. 检查类型是否匹配，判断指定的step是否允许写入
                metric.ensure_type_match(histogram.type)
                if metric.try_accept_step(histogram.step):
                    metric.update(histogram)
                    records.append(builder.build_histogram_record(self._counter, histogram))
                else:
                    console.debug(
                        f"Metric '{histogram.key}' at step {histogram.step} was skipped "
                        "because it is duplicate or too old."
                    )
        # 持久化存储record
        self._store_records(records)
        return records

    def _upsert_histograms_when_offline(self, histograms: List[HistogramRecord]) -> None:
        self._upsert_histograms_to_metrics(histograms)

    # ---- upsert_logs ----

    def upsert_logs(self, logs: List[LogRecord]) -> None:
        if not self._active:
            console.warning("Core is not active, refusing to upsert logs")
            return
        return super().upsert_logs(logs)

    def _upsert_logs_when_offline(self, logs: List[LogRecord]) -> None:
        records = [builder.build_log_record(self._counter, self._epoch, c) for c in logs]
        self._store_records(records)
        if records:
            action = "Skipped storing" if self._ctx.config.skip_store else "Stored"
            console.debug(
                f"{action} log records locally: count={len(records)}, nums={records[0].num}..{records[-1].num}",
                write_to_tty=False,
            )

    # ---- upsert_saves ----

    def upsert_saves(self, saves: List[SaveRecord]) -> None:
        if not self._active:
            console.warning("Core is not active, refusing to upsert saves")
            return
        if self._mode == "disabled":
            return self._upsert_saves_when_disabled(saves)
        # 内部保存（如config、metadata等）和用户保存（文件保存）共用 SaveRecord 结构
        # 1. 区分内部保存和用户保存
        custom_saves: List[SaveRecord] = []
        internal_saves: List[SaveRecord] = []
        for save in saves:
            if save.type == SaveType.SAVE_TYPE_CUSTOM:
                custom_saves.append(save)
            else:
                internal_saves.append(save)
        # 2. 执行内部保存的本地持久化
        if internal_saves:
            records = [builder.build_save_record(self._counter, s, s.type) for s in internal_saves]
            self._store_records(records)
        # 3. 执行用户保存的逻辑
        if custom_saves:
            self._upsert_saves_when_offline(custom_saves)

    def _handle_custom_save(self, saves: List[SaveRecord]) -> List[Record]:
        # skip_store：不创建本地镜像软链接（不触碰 files_dir、不填 target_path），无文件监听
        if not self._ctx.config.skip_store:
            assert self._watcher is not None, "watcher must be initialized before upsert"
            linked = create_save_links(saves, self._ctx.files_dir)
            if linked > 0:
                console.info(
                    f"Symlinked {linked} files into the OpenRunLab run directory; call open_run_lab.save again to sync new files."
                )
            self._watcher.register_live_watches(saves, self._ctx.files_dir)
        records = [builder.build_save_record(self._counter, s) for s in saves]
        self._store_records(records)
        return records

    def _upsert_saves_when_offline(self, saves: List[SaveRecord]) -> None:
        self._handle_custom_save(saves)

    def _on_file_changed(self, save_record: SaveRecord) -> None:
        """FileWatcher 回调：持久化。"""
        if not self._active or self._store is None:
            return
        records = [builder.build_save_record(self._counter, save_record)]
        self._store_records(records)

    # ---------------------------------- fork 方法 ----------------------------------

    def fork(self) -> "CorePython":
        raise RuntimeError("CorePython.fork() should not be called (designed for orlab-core).")

    # ---------------------------------- finish 方法 ----------------------------------

    def deliver_run_finish(self, finish_request: DeliverRunFinishRequest) -> DeliverRunFinishResponse:
        if not self._active:
            return DeliverRunFinishResponse(success=False, message="Run is not active, refusing to finish.")
        resp = super().deliver_run_finish(finish_request)
        self._active = False
        return resp

    def _store_finish(self, finish_record: FinishRecord) -> Optional[Record]:
        assert self._store is not None, "store must be initialized before shutdown"
        # 1. 构建结束记录并写入存储
        record = builder.build_finish_record(finish_record)
        record.finish.CopyFrom(finish_record)
        log_record: Optional[Record] = None
        if finish_record.state != RunState.RUN_STATE_FINISHED:
            error_message = (
                finish_record.error
                if finish_record.error
                else "run failed with unknown error while finish_record.error is not set"
            )
            log_record = builder.build_log_record(
                self._counter,
                self._epoch,
                LogRecord(
                    timestamp=finish_record.finished_at,
                    level=LogLevel.LOG_LEVEL_ERROR,
                    line=error_message,
                ),
            )
        # 2. 关闭存储、文件监视器等本地资源，停止接受新的记录
        self._store_records([record])
        self._release_local_storage()
        return log_record

    def _release_local_storage(self) -> None:
        """关闭本地存储与文件监听；两者独立释放，失败时抛出首个异常。"""
        store, self._store = self._store, None
        watcher, self._watcher = self._watcher, None
        errors: List[BaseException] = []
        if store is not None:
            with safe.block(message="Failed to close local storage", on_error=errors.append):
                store.close()
        if watcher is not None:
            with safe.block(message="Failed to stop file watcher", on_error=errors.append):
                watcher.stop()
        if errors:
            raise errors[0]

    def _finish_when_offline(self, finish_request: DeliverRunFinishRequest) -> DeliverRunFinishResponse:
        self._store_finish(finish_request.finish_record)
        return DeliverRunFinishResponse(success=True, message="OK, but use offline")

    # ---------------------------------- 确认完成 ----------------------------------

    def _confirm_finish_when_enabled(self) -> ConfirmRunFinishResponse:
        # 纯本地模式下，deliver_run_finish 已完成全部收尾工作
        return ConfirmRunFinishResponse(success=True, message="OK")
