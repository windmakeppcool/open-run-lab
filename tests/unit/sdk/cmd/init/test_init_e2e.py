"""
@author: cunyue
@file: test_init_e2e.py
@time: 2026/3/14
@description: 测试 swanlab.init() 的端到端行为（纯本地版本）

测试分组：
  - TestInitDisabledMode     : disabled 模式，无文件系统写入
  - TestInitOfflineMode      : offline 模式，验证目录创建与本地落盘
  - TestInitReinit           : reinit 参数行为（跳过/重建）
  - TestInitSettingsPriority : 配置优先级（全局 < 自定义 < 传参）
  - TestInitFactoryDispatch  : 验证 factory 模式按模式分派组件类型
  - TestRunSave              : run.save() 在 offline 模式下的本地镜像行为
"""

import json
from typing import cast

import pytest
import responses

from swanlab.sdk.cmd.init import init
from swanlab.sdk.cmd.merge_settings import merge_settings
from swanlab.sdk.internal.bus import RunEmitter
from swanlab.sdk.internal.run import has_run
from swanlab.sdk.internal.run.components import BackgroundConsumer, NullConsumer, NullEmitter
from swanlab.sdk.internal.settings import Settings, create_settings
from swanlab.sdk.typings.run import ModeType


class TestInitDisabledMode:
    def test_init_returns_run_instance(self):
        run = init(mode="disabled")
        assert run is not None
        assert has_run() is True
        run.finish()

    def test_init_does_not_create_log_dir(self):
        """disabled 模式不应创建日志目录"""
        run = init(mode="disabled")
        log_dir = run._ctx.config.settings.log_dir
        assert not log_dir.exists()
        run.finish()

    def test_init_workspace_is_none_by_default(self):
        run = init(mode="disabled")
        assert run._ctx.config.settings.project.workspace is None
        run.finish()

    def test_init_custom_workspace_is_preserved(self):
        run = init(mode="disabled", workspace="my-workspace")
        assert run._ctx.config.settings.project.workspace == "my-workspace"
        run.finish()


class TestInitOfflineMode:
    def test_init_creates_log_dir_with_gitignore(self):
        """offline 模式应创建日志目录，并在首次创建时写入 .gitignore"""
        run = init(mode="offline")
        log_dir = run._ctx.config.settings.log_dir

        assert log_dir.exists()
        assert (log_dir / ".gitignore").exists()

    def test_init_creates_run_subdirs(self):
        """offline 模式应创建 run_dir、media_dir、files_dir、debug_dir"""
        run = init(mode="offline")
        ctx = run._ctx

        assert ctx.run_dir.exists()
        assert ctx.media_dir.exists()
        assert ctx.files_dir.exists()
        assert ctx.debug_dir.exists()

    def test_init_workspace_is_none_by_default(self):
        run = init(mode="offline")
        assert run._ctx.config.settings.project.workspace is None

    def test_init_auto_generates_name_and_color(self):
        """未传 name/color 时，应自动生成非空字符串"""
        run = init(mode="offline")
        s = run._ctx.config.settings

        assert s.experiment.name
        assert s.experiment.color

    def test_init_preserves_custom_experiment_name(self):
        run = init(mode="offline", name="test-save-exp")
        assert run._ctx.config.settings.experiment.name == "test-save-exp"

    def test_init_writes_local_store_on_finish(self):
        """offline 模式 log 后 finish，应留下本地 store 文件"""
        run = init(mode="offline")
        run.log({"loss": 0.5})
        run_file = run._ctx.run_file
        run.finish()

        assert run_file.exists()

    @responses.activate
    def test_init_sends_webhook_with_path_run_dir(self):
        """offline init 发送 webhook 时应支持真实上下文中的 Path run_dir。"""
        webhook_url = "https://example.com/webhook"
        webhook_settings = Settings.model_validate(
            {
                "integration": {
                    "webhook": {
                        "url": webhook_url,
                        "value": "test_webhook_value",
                        "timeout": 5,
                    }
                },
                "probe": {"monitor": False},
            }
        )

        responses.add(responses.POST, webhook_url, status=200)
        run = init(mode="offline", project="webhook-project", settings=webhook_settings)
        assert len(responses.calls) == 1
        payload = json.loads(responses.calls[0].request.body)  # type: ignore[arg-type]
        assert payload["swanlab"]["mode"] == "offline"
        assert payload["swanlab"]["run_dir"] == str(run._ctx.run_dir)
        run.finish()


class TestInitReinit:
    def test_reinit_false_raises_when_run_exists(self):
        run = init(mode="disabled")
        with pytest.raises(RuntimeError, match="requires an inactive Run"):
            init(mode="disabled", reinit=False)
        run.finish()

    def test_reinit_true_creates_new_run(self):
        first = init(mode="offline")
        second = init(mode="offline", reinit=True)

        assert second is not first
        assert has_run() is True
        second.finish()


class TestInitSettingsPriority:
    def test_args_override_global_settings(self):
        merge_settings({"project": {"name": "global-project"}})

        run = init(mode="disabled", project="arg-project")

        assert run._ctx.config.settings.project.name == "arg-project"
        run.finish()

    def test_custom_settings_override_global(self):
        merge_settings({"project": {"name": "global-project"}})
        custom = Settings(project=Settings.Project(name="custom-project"))

        run = init(mode="disabled", settings=custom)

        assert run._ctx.config.settings.project.name == "custom-project"
        run.finish()


class TestInitFactoryDispatch:
    """验证 init() 创建的 Run 对象内部组件类型符合 factory 设计约定"""

    def test_disabled_uses_null_components(self):
        run = init(mode="disabled")
        assert isinstance(run._components.emitter, NullEmitter)
        assert isinstance(run._components.consumer, NullConsumer)
        run.finish()

    @pytest.mark.parametrize("mode", ["offline"])
    def test_offline_uses_runtime_components(self, mode):
        run = init(mode=cast(ModeType, mode))
        assert isinstance(run._components.emitter, RunEmitter)
        assert isinstance(run._components.consumer, BackgroundConsumer)
        run.finish()


class TestRunSave:
    def test_save_offline_mode_creates_symlink(self, tmp_path):
        """offline 模式下 save() 应在 files_dir 中创建 symlink"""
        run = init(mode="offline")
        checkpoint = tmp_path / "model.pt"
        checkpoint.write_text("weights", encoding="utf-8")

        result = run.save("model.pt", base_path=str(tmp_path), policy="now")
        assert result == ["model.pt"]

        run.finish()
        # finish() 等待 consumer drain，symlink 应已创建
        link_path = run._ctx.files_dir / "model.pt"
        assert link_path.exists()

    def test_save_no_match_returns_empty_list(self, tmp_path):
        run = init(mode="offline")
        result = run.save("*.bin", base_path=str(tmp_path), policy="now")
        assert result == []
        run.finish()


def test_create_settings_snapshot_is_independent():
    merge_settings({"project": {"name": "snapshot-project"}})
    first = create_settings()
    second = create_settings()
    assert first is not second
    assert first.project.name == "snapshot-project"
    assert second.project.name == "snapshot-project"


def test_run_finish_clears_global_run():
    run = init(mode="offline")
    assert has_run() is True
    run.finish()
    assert has_run() is False


def test_init_accepts_callback_instances():
    """callbacks 参数应接受合法 Callback 实例（不做网络请求）"""
    from swanlab.sdk.protocol import Callback

    class _NoopCallback(Callback):
        @property
        def name(self) -> str:
            return "NoopCallback"

    run = init(mode="offline", callbacks=[_NoopCallback()])
    run.finish()
