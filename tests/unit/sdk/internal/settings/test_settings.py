"""
@author: cunyue
@file: test_settings.py
@time: 2026/3/5 15:56
@description: 测试 SwanLabSettings 基本方法（纯本地版本）
"""

import os
from pathlib import Path

import pytest
from pydantic_settings import SettingsConfigDict

from swanlab.sdk.internal.settings import Settings


@pytest.fixture(autouse=True)
def isolate_global_env(tmp_path, monkeypatch):
    """全局环境隔离：将配置根目录指向 tmp_path，避免读取开发者本机配置。"""
    monkeypatch.setenv("SWANLAB_SAVE_DIR", str(tmp_path))
    monkeypatch.delenv("SWANLAB_API_KEY", raising=False)
    monkeypatch.delenv("SWANLAB_API_HOST", raising=False)
    monkeypatch.delenv("SWANLAB_WEB_HOST", raising=False)


def test_path_validation(tmp_path):
    """测试默认值加载，以及路径是否会自动创建"""
    settings = Settings(log_dir=Path(tmp_path) / "log")
    # log_dir 不会自动创建
    assert not settings.log_dir.exists()


def test_priority_yaml_over_env(tmp_path, monkeypatch):
    """测试优先级：本地 YAML > 环境变量"""

    # 设置低优先级的环境变量
    monkeypatch.setenv("SWANLAB_PROBE_MONITOR", "false")

    s1 = Settings()
    assert s1.probe.monitor is False

    # 创建高优先级的 swanlab.yaml
    yaml_content = "log_dir: ./custom_log\nprobe:\n  monitor: true"
    (tmp_path / "swanlab.yaml").write_text(yaml_content)

    s2 = Settings()
    assert s2.log_dir.name == "custom_log"
    assert s2.probe.monitor is True


class TestConfigSourcePriority:
    """测试配置源优先级：user config / pwd config / 当前目录 swanlab.yaml"""

    def test_root_config_yaml_priority(self, tmp_path):
        """root/config.yaml 优先于默认值"""
        config_file = tmp_path / "config.yaml"
        config_file.write_text("mode: disabled\nlog_dir: ./root_log")

        settings = Settings()
        assert settings.mode == "disabled"
        assert settings.log_dir.name == "root_log"

    def test_pwd_swanlab_config_yaml_priority(self, tmp_path, monkeypatch):
        """pwd/.swanlab/config.yaml 生效"""
        monkeypatch.chdir(tmp_path)
        swanlab_dir = tmp_path / ".swanlab"
        swanlab_dir.mkdir()
        (swanlab_dir / "config.yaml").write_text("mode: disabled\nlog_dir: ./pwd_log")

        settings = Settings()
        assert settings.mode == "disabled"
        assert settings.log_dir.name == "pwd_log"

    def test_pwd_config_over_root_config(self, tmp_path, monkeypatch):
        """pwd/.swanlab/config.yaml 优先级高于 root/config.yaml"""
        monkeypatch.chdir(tmp_path)

        (tmp_path / "config.yaml").write_text("mode: disabled\nlog_dir: ./root_log")

        swanlab_dir = tmp_path / ".swanlab"
        swanlab_dir.mkdir()
        (swanlab_dir / "config.yaml").write_text("log_dir: ./pwd_log")

        settings = Settings()
        assert settings.log_dir.name == "pwd_log"
        # mode 来自 root/config.yaml（pwd 配置未覆盖）
        assert settings.mode == "disabled"

    def test_swanlab_yaml_over_pwd_config(self, tmp_path, monkeypatch):
        """当前目录 swanlab.yaml 优先级高于 pwd/.swanlab/config.yaml"""
        monkeypatch.chdir(tmp_path)

        swanlab_dir = tmp_path / ".swanlab"
        swanlab_dir.mkdir()
        (swanlab_dir / "config.yaml").write_text("mode: disabled\nlog_dir: ./pwd_log")

        (tmp_path / "swanlab.yaml").write_text("log_dir: ./local_yaml_log")

        settings = Settings()
        assert settings.log_dir.name == "local_yaml_log"
        # mode 来自 pwd/.swanlab/config.yaml（swanlab.yaml 未覆盖）
        assert settings.mode == "disabled"

    def test_root_config_yml_extension(self, tmp_path):
        """root/config.yml 也能被正确加载"""
        (tmp_path / "config.yml").write_text("log_dir: ./yml_log")

        settings = Settings()
        assert settings.log_dir.name == "yml_log"

    def test_pwd_config_yml_extension(self, tmp_path, monkeypatch):
        """pwd/.swanlab/config.yml 也能被正确加载"""
        monkeypatch.chdir(tmp_path)
        swanlab_dir = tmp_path / ".swanlab"
        swanlab_dir.mkdir()
        (swanlab_dir / "config.yml").write_text("log_dir: ./yml_log")

        settings = Settings()
        assert settings.log_dir.name == "yml_log"

    def test_root_config_not_exists(self):
        """root 目录下没有 config.yaml 时不影响正常加载"""
        settings = Settings()
        assert settings.mode == "offline"

    def test_pwd_config_not_exists(self, tmp_path, monkeypatch):
        """pwd/.swanlab 目录不存在时不影响正常加载"""
        monkeypatch.chdir(tmp_path)

        settings = Settings()
        assert settings.mode == "offline"


def test_merge_settings_dict_deep_update():
    """测试字典合并，确保深层嵌套不会被覆盖"""
    settings = Settings()

    settings.merge_settings({"probe": {"monitor": False}})

    assert settings.probe.monitor is False
    assert settings.probe.monitor_interval == 10
    assert settings.log_dir.name == "swanlog"


def test_merge_settings_object_exclude_unset(tmp_path, monkeypatch):
    """测试对象合并，确保未设置的默认值不会覆盖已有配置"""
    monkeypatch.chdir(tmp_path)
    settings = Settings(log_dir=Path("./current_log"))

    new_settings = Settings(log_dir=Path("./new_log"))
    settings.merge_settings(new_settings)

    assert settings.log_dir.name == "new_log"  # 新配置生效
    assert settings.probe.monitor is True  # 原配置未被默认值覆盖


def test_secrets_loading(tmp_path):
    """测试本地 secret 文件读取"""
    secrets_dir = tmp_path / "secrets"
    secrets_dir.mkdir()
    (secrets_dir / "mode").write_text("disabled")

    class TestSettings(Settings):
        model_config = SettingsConfigDict(secrets_dir=str(secrets_dir))

    settings = TestSettings()
    assert settings.mode == "disabled"


def test_mode_validation():
    """测试 mode 字段的校验，纯本地版本只允许 offline / disabled"""
    assert Settings().mode == "offline"
    assert Settings(mode="offline").mode == "offline"
    assert Settings(mode="disabled").mode == "disabled"

    for invalid in ("online", "local", "cloud", "invalid"):
        with pytest.raises(ValueError, match="Invalid mode"):
            Settings(mode=invalid)  # type: ignore[arg-type]


def test_mode_env_override(monkeypatch):
    monkeypatch.setenv("SWANLAB_MODE", "disabled")
    assert Settings().mode == "disabled"


def test_core_section_rule_env_overrides_legacy(monkeypatch):
    """测试新版 core section rule 环境变量优先于旧版环境变量"""
    monkeypatch.setenv("SWANLAB_CORE_SECTION_RULE", "-1")
    monkeypatch.setenv("SWANLAB_SECTION_RULE_IDX", "1")

    settings = Settings()

    assert settings.core.section_rule == -1


class TestSkipStore:
    """core.skip_store 在纯本地版本下允许配置"""

    def test_default_false(self):
        assert Settings().core.skip_store is False

    def test_enabled_passes(self):
        settings = Settings(mode="offline", core=Settings.Core(skip_store=True))
        assert settings.core.skip_store is True

    def test_env_var_enables(self, monkeypatch):
        monkeypatch.setenv("SWANLAB_CORE_SKIP_STORE", "true")
        assert Settings().core.skip_store is True

    def test_to_core_proto_passthrough(self, tmp_path):
        settings = Settings(mode="offline", core=Settings.Core(skip_store=True))
        proto = settings.to_core_proto(run_id="r1", run_dir=tmp_path)
        assert proto.skip_store is True


def test_no_cloud_credentials_fields():
    """纯本地版本不再暴露云端连接配置"""
    for field in ("api_key", "api_host", "web_host", "on_online_error"):
        assert field not in Settings.model_fields


def test_environment_isolation(tmp_path):
    """确认测试环境的 SWANLAB_SAVE_DIR 生效"""
    assert os.environ["SWANLAB_SAVE_DIR"] == str(tmp_path)
