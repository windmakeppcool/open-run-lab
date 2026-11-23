"""SwanLab Core settings."""

from pydantic import BaseModel, ConfigDict, Field

from .compat import section_rule_index_factory


class CoreSettings(BaseModel):
    """
    Slash index used to split a metric key into section name and metric name.
    0 means the first slash, 1 means the second slash, -1 means the last slash.
    Out-of-range values wrap via ``idx % slash_count``.
    The split position is fixed when settings are loaded for each run.
    """

    section_rule: int = Field(default_factory=section_rule_index_factory)
    """
    Section rule for auto generated section name.
    """
    record_batch: int = Field(default=10_000, gt=0, lt=100_000)
    """
    Batch size of records per dispatch. Default 10000.

    纯本地版本不再有网络分片，此字段仅为兼容 CoreSettings proto 保留。
    """
    record_interval: float = Field(default=1.5, gt=0)
    """
    Batch interval (seconds). Default 1.5s.

    纯本地版本不再有上传线程，此字段仅为兼容 CoreSettings proto 保留。
    """
    save_split: int = Field(default=100 * 1024 * 1024)
    """
    File size threshold in bytes for splitting. Default 100 MiB.

    纯本地版本不再有分片上传，此字段仅为兼容 CoreSettings proto 保留。
    """
    save_size: int = Field(default=50 * 1024 * 1024 * 1024)
    """
    Maximum saved size per file. Default 50 GiB.
    """
    save_part: int = Field(default=32 * 1024 * 1024, gt=0)
    """
    Part size in bytes. Default 32 MiB.

    纯本地版本不再有分片上传，此字段仅为兼容 CoreSettings proto 保留。
    """
    save_batch: int = Field(default=100)
    """
    Maximum number of files per save batch. Default 100.
    """
    skip_store: bool = Field(default=False)
    """
    跳过所有 SDK 本地文件写入。

    纯本地版本下开启后不会产生任何可供 swanlab-console 查看的数据，
    通常只用于完全关闭持久化的场景。
    """
    model_config = ConfigDict(frozen=True)
