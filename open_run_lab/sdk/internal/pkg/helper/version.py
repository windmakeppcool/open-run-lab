"""
@author: cunyue
@file: version.py
@time: 2026/4/12 01:19
@description: OpenRunLab SDK 版本工具
"""

import json
from pathlib import Path
from typing import Optional

import requests

from open_run_lab.sdk.internal.pkg import safe

package_path = Path(__file__).resolve().parents[4] / "package.json"


def get_orlab_version() -> str:
    """获取 OpenRunLab 的版本号
    :return: OpenRunLab 的版本号
    """
    # 读取package.json文件
    with open(package_path, "r") as f:
        return json.load(f)["version"]


@safe.decorator(level="debug", message="Failed to fetch open-run-lab latest version")
def get_orlab_latest_version(timeout=1, url="https://pypi.org/pypi/open-run-lab/json") -> Optional[str]:
    """
    获取 open-run-lab 的最新版本号
    :param timeout: 请求超时时间
    :param url: PyPI API URL
    :return: 最新版本号
    """
    response = requests.get(url, timeout=timeout)
    if response.status_code == 200:
        data = response.json()
        return data["info"]["version"]
    else:
        return None
