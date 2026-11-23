"""
OpenRunLab notification callbacks.

Each callback runs IO (HTTP/SMTP) in a shared background thread pool so the
training main process is never blocked.  Exceptions are isolated by the
CallbackManager's ``safe.block`` dispatcher — individual callback failures
do not affect other callbacks or the training loop.
"""

from open_run_lab.plugin.notification.bark import BarkCallback
from open_run_lab.plugin.notification.base import NotificationCallback
from open_run_lab.plugin.notification.dingtalk import DingTalkCallback
from open_run_lab.plugin.notification.discord import DiscordCallback
from open_run_lab.plugin.notification.email import EmailCallback
from open_run_lab.plugin.notification.lark import LarkCallback
from open_run_lab.plugin.notification.slack import SlackCallback
from open_run_lab.plugin.notification.telegram import TelegramCallback
from open_run_lab.plugin.notification.wecom import WeComCallback, WXWorkCallback

__all__ = [
    "LarkCallback",
    "DingTalkCallback",
    "WeComCallback",
    "WXWorkCallback",
    "DiscordCallback",
    "SlackCallback",
    "TelegramCallback",
    "EmailCallback",
    "BarkCallback",
    "NotificationCallback",
]
