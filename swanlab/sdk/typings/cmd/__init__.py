"""
@author: cunyue
@file: __init__.py
@time: 2026/4/15 23:35
@description: SwanLab SDK cmd 模块的类型定义和导出
"""

import os
from typing import Any, Dict, Union

ConfigLike = Union[Dict[str, Any], str, os.PathLike]
"""
swanlab.init 允许传入的配置类型
"""
