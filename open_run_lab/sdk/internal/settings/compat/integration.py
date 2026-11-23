"""集成域遗留环境变量兼容层。"""

from .env import getenv

__all__ = [
    "webhook_timeout_factory",
    "webhook_url_factory",
    "webhook_value_factory",
]


def webhook_url_factory() -> str:
    # 使用额外的 ORLAB_WEBHOOK 环境变量，一方面是为了向下兼容（老版本是 ORLAB_WEBHOOK），另一方面是自动生成的环境变量太长了
    return getenv("ORLAB_WEBHOOK", "")


def webhook_value_factory() -> str:
    # 使用额外的 ORLAB_WEBHOOK_VALUE 环境变量，一方面是为了向下兼容（老版本是 ORLAB_WEBHOOK_VALUE），另一方面是自动生成的环境变量太长了
    return getenv("ORLAB_WEBHOOK_VALUE", "")


def webhook_timeout_factory() -> int:
    # 使用额外的 ORLAB_WEBHOOK_TIMEOUT 环境变量，因为自动生成的环境变量太长了
    return int(getenv("ORLAB_WEBHOOK_TIMEOUT", "5"))
