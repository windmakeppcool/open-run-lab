"""
@file: test_run_e2e.py
@description: 测试 open_run_lab.run 属性的端到端行为
全部使用 mode='disabled'，避免文件系统和网络依赖。
"""

import open_run_lab
from open_run_lab.sdk.cmd.init import init
from open_run_lab.sdk.cmd.run import finish
from open_run_lab.sdk.internal.run import Run


class TestRunAttributeE2E:
    def test_run_is_none_before_init(self):
        """未调用 init() 时，open_run_lab.run 应为 None"""
        assert open_run_lab.run is None

    def test_run_is_orlab_run_after_init(self):
        """init() 之后，open_run_lab.run 应返回活跃的 Run 实例"""
        run = init(mode="disabled")
        assert open_run_lab.run is not None
        assert isinstance(open_run_lab.run, Run)
        assert open_run_lab.run is run
        finish()

    def test_run_equals_get_run(self):
        """init() 之后，open_run_lab.run 应与 open_run_lab.get_run() 返回同一对象"""
        init(mode="disabled")
        assert open_run_lab.run is open_run_lab.get_run()
        finish()

    def test_run_is_none_after_finish(self):
        """finish() 之后，open_run_lab.run 应重新变为 None"""
        run1 = init(mode="disabled")
        assert open_run_lab.run is not None
        finish()
        assert open_run_lab.run is None
        run2 = init(mode="disabled")
        assert open_run_lab.run is not None
        assert open_run_lab.run is run2
        assert run1 is not run2
