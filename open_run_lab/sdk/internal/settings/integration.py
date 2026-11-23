"""
@author: cunyue
@file: integration.py
@time: 2026/3/5 20:25
@description: OpenRunLab 集成配置，配置 OpenRunLab 与外部系统的集成
"""

from typing import ClassVar, Type

from pydantic import BaseModel, Field, model_validator
from pydantic.config import ConfigDict

from .compat import (
    webhook_timeout_factory,
    webhook_url_factory,
    webhook_value_factory,
)


class WebhookSettings(BaseModel):
    url: str = Field(default_factory=webhook_url_factory)
    """
    Webhook URL for OpenRunLab notifications.
    """

    value: str = Field(default_factory=webhook_value_factory)
    """
    Webhook value for OpenRunLab notifications.
    """

    timeout: int = Field(default_factory=webhook_timeout_factory)
    """
    Webhook timeout for OpenRunLab notifications.
    """
    model_config = ConfigDict(frozen=True)


class IntegrationSettings(BaseModel):
    """
    Configuration for OpenRunLab integrations.
    """

    Webhook: ClassVar[Type[WebhookSettings]] = WebhookSettings

    webhook: WebhookSettings = Field(default_factory=WebhookSettings)

    @model_validator(mode="before")
    @classmethod
    def assemble_nested_env(cls, data: dict) -> dict:
        """
        拦截 Pydantic 因 max_split=1 截断生成的平铺环境变量，
        将其重新组装为嵌套字典，以适配内部结构。
        """
        if isinstance(data, dict):
            # 处理 webhook_xxx -> webhook: {xxx: ...}
            webhook_data = data.get("webhook", {})
            if isinstance(webhook_data, dict):
                has_update = False
                for key in list(data.keys()):
                    if key.startswith("webhook_"):
                        webhook_data[key[8:]] = data.pop(key)
                        has_update = True
                if has_update:
                    data["webhook"] = webhook_data

        return data

    model_config = ConfigDict(frozen=True)
