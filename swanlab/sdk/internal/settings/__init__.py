"""
@author: cunyue
@file: __init__.py
@time: 2026/3/5 14:38
@description: SwanLab 包配置项，根据优先级从低到高加载配置：
1. 默认值
2. 系统目录下的配置文件
3. 环境变量
4. 当前目录下 .env 文件
5. /etc/swanlab/*.{yaml,yml}
6. 当前目录下 swanlab.{yaml,yml}
7. 本地 secret 配置文件目录

在设计上 Settings 仅是与用户交互的配置入口，不包含业务逻辑，这意味着仅检查必要的类型和格式和必要的默认值，不产生副作用：
1. 文件夹创建
2. 具体业务逻辑，如实验id生成与格式校验、实验名称长度校验等

用户可以通过merge_settings动态合并配置，但是在设计上，在执行`swanlab.init`和`swanlab.finish`之间，无法使用merge_settings。
"""

from pathlib import Path
from typing import Any, ClassVar, Dict, Optional, Tuple, Type, Union, get_args

import yaml
from pydantic import Field, field_validator
from pydantic.functional_validators import model_validator
from pydantic_settings import (
    BaseSettings,
    EnvSettingsSource,
    PydanticBaseSettingsSource,
    SecretsSettingsSource,
    SettingsConfigDict,
    YamlConfigSettingsSource,
)

from swanlab.proto.swanlab.settings.core.v1.core_pb2 import CoreSettings as CoreSettingsPb
from swanlab.proto.swanlab.settings.probe.v1.probe_pb2 import ProbeSettings as ProbeSettingsPb
from swanlab.sdk.internal.pkg import console, helper
from swanlab.sdk.typings.run import ModeType

from .compat import getenv, log_dir_factory, strip_env_quotes
from .core import CoreSettings
from .experiment import ExperimentSettings, ProjectSettings, RunSettings
from .global_settings import get_global_settings, set_global_settings
from .integration import IntegrationSettings
from .probe import ProbeSettings
from .terminal import TerminalSettings

__all__ = ["Settings", "create_settings", "set_global_settings"]


ROOT_FOLDER = ".swanlab"
# 根据环境变量自动设置 secrets_dir
# 如果强制设置，会出现警告：https://github.com/pydantic/pydantic/issues/2175
secrets_dir_env = getenv("SWANLAB_SECRETS_DIR")
SECRETS_DIR: Optional[str] = secrets_dir_env or None

# 根据环境变量选择全局配置文件路径
config_dir_env = getenv("SWANLAB_CONFIG_DIR")
CONFIG_DIR: str = config_dir_env or "/etc/swanlab"


class _QuoteAwareEnvSettingsSource(EnvSettingsSource):
    """环境变量源：在加载阶段剥离 shell 脚本注入的成对引号。

    通过在 ``__init__`` 末尾清洗 ``self.env_vars``，
    使后续所有消费路径（简单字段读取、嵌套字段 explode、复杂字段 JSON 解析）均获得清理后的值。

    NOTE: 剥离行为仅覆盖环境变量源；Secret 文件源（SecretsSettingsSource，读取本地挂载的
    secret 文件）不做引号剥离，文件内容中的字面引号会原样保留，属于已知限制。

    如果有需求，后续可以效仿 SWANLAB_CONFIG_DIR 等专门写一个 ``SWANLAB_STRIP_ENV_QUOTES`` 环境变量来控制是否启用剥离功能或者专门控制某几个key的剥离行为。
    """

    def __init__(self, settings_cls: Type[Any], **kwargs: Any) -> None:
        super().__init__(settings_cls, **kwargs)
        self.env_vars = {
            key: strip_env_quotes(val) if isinstance(val, str) else val for key, val in self.env_vars.items()
        }


class Settings(BaseSettings):
    """SwanLab configuration settings.

    This class manages all SwanLab configuration options, loaded from multiple sources
    in order of priority: defaults → environment variables → config files → user code.

    Use `swanlab.merge_settings()` to customize settings before calling `swanlab.init()`.

    Examples:

        Create custom settings:

        >>> from swanlab import Settings
        >>> from pathlib import Path
        >>> custom_settings = Settings(mode="offline", log_dir=Path("./my_logs"))
        >>> import swanlab
        >>> swanlab.merge_settings(custom_settings)
        >>> run = swanlab.init()

        Configure nested settings:

        >>> from swanlab import Settings
        >>> custom_settings = Settings(
        ...     mode="offline",
        ...     probe=Settings.Probe(monitor=False)
        ... )
        >>> import swanlab
        >>> swanlab.merge_settings(custom_settings)
    """

    @staticmethod
    def get_pwd_config_dir():
        return Path.cwd() / ROOT_FOLDER

    @staticmethod
    def get_user_config_dir():
        # SWANLAB_SAVE_DIR 用于向下兼容历史环境变量
        return Path(getenv("SWANLAB_ROOT") or getenv("SWANLAB_SAVE_DIR", str(Path.home() / ROOT_FOLDER)))

    Project: ClassVar[Type[ProjectSettings]] = ProjectSettings
    Run: ClassVar[Type[RunSettings]] = RunSettings
    Experiment: ClassVar[Type[ExperimentSettings]] = ExperimentSettings
    Terminal: ClassVar[Type[TerminalSettings]] = TerminalSettings
    Integration: ClassVar[Type[IntegrationSettings]] = IntegrationSettings
    Core: ClassVar[Type[CoreSettings]] = CoreSettings
    Probe: ClassVar[Type[ProbeSettings]] = ProbeSettings

    interactive: bool = True
    """
    Whether to enable interactive mode.
    If False, all user input prompts and related interactions will be disabled.
    Useful for CI/CD environments or background batch jobs.
    """

    mode: ModeType = "offline"
    """
    SwanLab Run mode.

    * `disabled`: Disable SwanLab.
    * `offline`: 将实验数据写入本地 swanlog 目录，可通过 swanlab-console 查看。
    """

    @field_validator("mode", mode="before")
    def validate_mode(cls, v: Any) -> ModeType:
        if v in list(get_args(ModeType)):
            return v
        raise ValueError(f"Invalid mode: {v}, allowed values are {list(get_args(ModeType))}")

    log_dir: Path = Field(default_factory=log_dir_factory, validate_default=True)
    """
    Directory for SwanLab logs.
    Semantically, this is just a path representation and the directory may NOT exist when loaded.
    The actual folder creation is deferred to the SDK initialization phase to avoid side effects.
    """

    @field_validator("log_dir", mode="before")
    def validate_log_dir(cls, v: Union[str, Path]) -> Path:
        """
        如果 log_dir 存在，必须是目录
        """
        if Path(v).exists() and not Path(v).is_dir():
            raise ValueError(f"Log directory {v} exists but is not a directory.")
        return Path(v)

    @model_validator(mode="before")
    @classmethod
    def strip_non_empty(cls, data: Dict) -> Dict:
        """
        删除空值和空字典，以适配传入None的情况，一般情况下此校验必须在其他model_validator之前定义
        如果出现部分字段需要识别None值，则在此校验之前定义model_validator
        """
        if isinstance(data, dict):
            data = helper.strip_none(data)
        return data

    @model_validator(mode="after")
    def _(self):
        """
        校验root目录必须存在
        """
        path_v = self.get_user_config_dir()

        if path_v.exists() and not path_v.is_dir():
            raise ValueError(
                f"Root path {path_v} exists but is not a directory.",
                "Please remove the file or choose a different path.",
            )
        return self

    project: ProjectSettings = Field(default_factory=ProjectSettings)
    """
    Configuration for the project of this SwanLab run.
    """
    experiment: ExperimentSettings = Field(default_factory=ExperimentSettings)
    """
    Configuration for the experiment of this SwanLab run.
    """
    run: RunSettings = Field(default_factory=RunSettings)
    """
    Configuration for the run of this SwanLab experiment.
    """
    terminal: TerminalSettings = Field(default_factory=TerminalSettings)
    """
    Configuration for SwanLab terminal log collection.
    """
    integration: IntegrationSettings = Field(default_factory=IntegrationSettings)
    """
    Configuration for SwanLab integrations, including webhook, etc.
    """
    core: CoreSettings = Field(default_factory=CoreSettings)
    """
    Configuration for core interaction limits (upload sizes, batch sizes, media limits, etc.).
    """
    probe: ProbeSettings = Field(default_factory=ProbeSettings)
    """
    Configuration for SwanLab Probe behavior.
    """

    model_config = SettingsConfigDict(
        env_prefix="SWANLAB_",
        env_nested_delimiter="_",
        env_file=".env",
        env_file_encoding="utf-8",
        env_nested_max_split=1,
        extra="ignore",
        frozen=True,
        # 指定 Secret 文件存放目录
        secrets_dir=SECRETS_DIR,
        validate_assignment=True,
        str_strip_whitespace=True,
    )

    def to_core_proto(self, run_id: str, run_dir: Path) -> CoreSettingsPb:
        return CoreSettingsPb(
            run_id=run_id,
            run_dir=str(run_dir.absolute()),
            section_rule=self.core.section_rule,
            record_batch=self.core.record_batch,
            record_interval=self.core.record_interval,
            save_split=self.core.save_split,
            save_size=self.core.save_size,
            save_part=self.core.save_part,
            save_batch=self.core.save_batch,
            skip_store=self.core.skip_store,
        )

    def to_probe_proto(
        self,
        run_id: Optional[str] = None,
        run_dir: Optional[Path] = None,
        global_system_step: Optional[int] = None,
    ) -> ProbeSettingsPb:
        ps = ProbeSettingsPb(
            hardware=self.probe.hardware,
            runtime=self.probe.runtime,
            requirements=self.probe.requirements,
            conda=self.probe.conda,
            git=self.probe.git,
            swanlab=self.probe.swanlab,
            monitor=self.probe.monitor,
            monitor_interval=self.probe.monitor_interval,
            monitor_disk_dir=str(self.probe.monitor_disk_dir.absolute()),
            skip_store=self.core.skip_store,
        )
        if run_id is not None:
            ps.run_id = run_id
        if run_dir is not None:
            ps.run_dir = str(run_dir.absolute())
        if global_system_step is not None:
            ps.global_system_step = global_system_step
        return ps

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: Type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> Tuple[PydanticBaseSettingsSource, ...]:
        # 优先级由高到低排列体现在返回的sources顺序：
        # 1. init_settings (merge_settings 传入的参数)
        # 2. 当前目录下 swanlab.{yaml,yml}
        # 3. /etc/swanlab/*.{yaml,yml}
        # 4. 当前目录下 .env 文件
        # 5. K8S/Docker 容器 Secret 配置项文件
        # 6. 环境变量
        # 7. 当前工作目录下 .swanlab/config.{yaml,yml}
        # 8. settings.get_user_config_dir() / config.{yaml,yml}
        # 9. 默认值 (Model Default)

        # 1. merge_settings 传入的参数
        sources = [init_settings]

        # 2. 当前目录下 swanlab.{yaml,yml}
        for ext in ["yaml", "yml"]:
            local_file = Path(f"swanlab.{ext}")
            if local_file.exists():
                sources.append(YamlConfigSettingsSource(settings_cls, yaml_file=local_file))

        # 3. /etc/swanlab/*.{yaml,yml}
        etc_dir = Path(CONFIG_DIR)
        if etc_dir.exists() and etc_dir.is_dir():
            etc_files = sorted(list(etc_dir.glob("*.yaml")) + list(etc_dir.glob("*.yml")), reverse=True)
            for file in etc_files:
                sources.append(YamlConfigSettingsSource(settings_cls, yaml_file=file))

        # 4. .env 文件
        sources.append(dotenv_settings)

        # 5. K8S/Docker 容器 Secret 配置项文件
        # 对于Secrets文件，不需要额外的前缀，直接使用默认的环境变量前缀
        secrets_dir = settings_cls.model_config.get("secrets_dir")
        if secrets_dir:
            custom_secret_source = SecretsSettingsSource(
                settings_cls,
                secrets_dir=secrets_dir,
                env_prefix="",
            )
            sources.append(custom_secret_source)
        # 优先级高于普通环境变量，防止敏感信息被低优先级的 Env 覆盖
        sources.append(file_secret_settings)

        # 6. 环境变量（剥离 shell 注入的成对引号）
        sources.append(_QuoteAwareEnvSettingsSource(settings_cls))

        # 7. 当前工作目录下 .swanlab/config.{yaml,yml}
        # 项目级别的配置文件，优先级高于环境变量但低于 .env
        pwd = cls.get_pwd_config_dir()
        if pwd.exists() and pwd.is_dir():
            for ext in ["yaml", "yml"]:
                config_file = pwd / f"config.{ext}"
                if config_file.exists():
                    console.debug(f"Loading settings from {config_file}")
                    sources.append(YamlConfigSettingsSource(settings_cls, yaml_file=config_file))

        # 8. settings.get_user_config_dir() / config.{yaml,yml}
        # 用户级别的全局配置文件，优先级最低（仅高于默认值）
        root_config_dir = cls.get_user_config_dir()
        if root_config_dir.exists() and root_config_dir.is_dir():
            for ext in ["yaml", "yml"]:
                config_file = root_config_dir / f"config.{ext}"
                if config_file.exists():
                    console.debug(f"Loading settings from {config_file}")
                    sources.append(YamlConfigSettingsSource(settings_cls, yaml_file=config_file))

        return tuple(sources)

    def to_yaml(self, *fields: str) -> str:
        """
        将当前 settings 序列化为 YAML 字符串。

        :param fields: 可选的字段名，可变参数。如果提供，仅输出这些字段；
                       如果字段不存在则跳过。支持嵌套字段名，如 "core.record_batch"。
                       如果未提供，输出所有字段。
        :return: YAML 格式的字符串
        """
        data = self._dump_and_filter(fields)
        return yaml.safe_dump(data, allow_unicode=True, default_flow_style=False, sort_keys=False)

    def save_to_yaml(self, target_dir: Union[str, Path], *fields: str, merge: bool = True) -> Path:
        """
        将当前 settings 保存为 YAML 文件到目标目录。

        如果目标目录下已存在 config.yaml 且 merge 为 True，则将现有配置与当前配置合并，
        当前配置的值会覆盖已有值。文件不存在或 merge 为 False 时直接写入。

        :param target_dir: 目标目录路径
        :param fields: 可选的字段名，仅保存指定字段；未提供则保存所有字段
        :param merge: 是否合并已存在的 config.yaml，默认为 True
        :return: 写入的文件路径
        """
        target_dir = Path(target_dir)
        target_file = target_dir / "config.yaml"

        data = self._dump_and_filter(fields)

        if merge and target_file.exists():
            with open(target_file, "r", encoding="utf-8") as f:
                existing = yaml.safe_load(f) or {}
            if isinstance(existing, dict):
                data = _deep_update(existing, data)

        # 确保目标目录存在
        target_dir.mkdir(parents=True, exist_ok=True)

        with open(target_file, "w", encoding="utf-8") as f:
            yaml.safe_dump(data, f, allow_unicode=True, default_flow_style=False, sort_keys=False)

        return target_file

    def _dump_and_filter(self, fields: Tuple[str, ...]) -> Dict[str, Any]:
        """导出数据并按字段过滤，同时转换 Path 为字符串"""
        data = self.model_dump()

        if fields:
            filtered: Dict[str, Any] = {}
            for field in fields:
                keys = field.split(".")
                src = data
                dst = filtered
                for i, key in enumerate(keys):
                    if isinstance(src, dict) and key in src:
                        if i == len(keys) - 1:
                            dst[key] = src[key]
                        else:
                            if key not in dst:
                                dst[key] = {}
                            dst = dst[key]
                            src = src[key]
                    else:
                        break
            data = filtered

        return self._convert_paths(data)

    @staticmethod
    def _convert_paths(obj: Any) -> Any:
        """递归将 Path 对象转换为字符串"""
        if isinstance(obj, Path):
            return str(obj)
        elif isinstance(obj, dict):
            return {k: Settings._convert_paths(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [Settings._convert_paths(item) for item in obj]
        return obj

    def merge_settings(self, other: Union["Settings", dict]) -> None:
        """
        合并自定义设置
        """
        if isinstance(other, self.__class__):
            # 1. 使用 exclude_unset=True 提取用户显式设置的字段
            # 这样可以确保 SwanLabSettings("log_dir"="...") 不会带上默认的值
            update_data = other.model_dump(exclude_unset=True)
        elif isinstance(other, dict):
            update_data = other
        else:
            raise TypeError(f"Only {self.__class__.__name__} or dict can be merged, not {type(other)}")

        # 2. 获取当前实例的完整状态字典
        current_data = self.model_dump()

        # 3. 递归合并数据 (确保嵌套的 dict 如 collect.metadata 不会被整个替换)
        merged_data = _deep_update(current_data, update_data)

        # 4. 验证新数据：通过类构造函数生成临时实例以触发校验和 Path 转换
        # 这一步能确保传入的路径字符串被 field_validator 处理成 Path 对象并创建目录
        validated_instance = self.__class__(**merged_data)

        # 5. 更新当前单例
        for field_name in self.__class__.model_fields.keys():
            new_value = getattr(validated_instance, field_name)
            # 绕过 frozen=True 的限制
            object.__setattr__(self, field_name, new_value)

        # 由于我们 绕过了 frozen=True 的限制，需要手动同步 __pydantic_fields_set__
        object.__setattr__(self, "__pydantic_fields_set__", validated_instance.__pydantic_fields_set__)


def _deep_update(base_dict: dict, update_dict: dict) -> dict:
    """递归合并字典，用于嵌套模型的 merge_settings"""
    for k, v in update_dict.items():
        if k in base_dict and isinstance(base_dict[k], dict) and isinstance(v, dict):
            base_dict[k] = _deep_update(base_dict[k], v)
        else:
            base_dict[k] = v
    return base_dict


def create_settings() -> Settings:
    """
    创造一个配置实例，继承全局配置，如果全局配置不存在则忽略
    """
    this_settings = Settings()
    global_settings = get_global_settings()
    if global_settings is not None:
        this_settings.merge_settings(global_settings)
    return this_settings
