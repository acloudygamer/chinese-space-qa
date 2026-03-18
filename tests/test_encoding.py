"""
测试: 编码设置模块
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from _encoding import setup_encoding


class TestEncoding:
    """编码设置测试"""

    def test_setup_encoding_win32(self, monkeypatch):
        """测试 Windows 下的编码设置"""
        # 模拟 Windows 平台
        monkeypatch.setattr(sys, "platform", "win32")
        # 模拟 stdout 行为
        import io

        mock_buffer = io.BytesIO()
        mock_stdout = io.TextIOWrapper(mock_buffer, encoding="utf-8")
        monkeypatch.setattr(sys, "stdout", mock_stdout)

        # 不应抛出异常
        setup_encoding()

    def test_setup_encoding_non_win32(self, monkeypatch):
        """测试非 Windows 平台"""
        monkeypatch.setattr(sys, "platform", "linux")
        # 应直接返回，不做处理
        setup_encoding()

    def test_setup_encoding_no_buffer(self, monkeypatch):
        """测试 stdout 无 buffer 属性"""
        monkeypatch.setattr(sys, "platform", "win32")

        class NoBufferStdout:
            buffer = None

        monkeypatch.setattr(sys, "stdout", NoBufferStdout())

        # 不应抛出异常
        setup_encoding()

    def test_setup_encoding_exception_handling(self, monkeypatch):
        """测试异常处理路径"""
        monkeypatch.setattr(sys, "platform", "win32")

        class BadStdout:
            buffer = True

            def __getattr__(self, name):
                raise RuntimeError("模拟异常")

        monkeypatch.setattr(sys, "stdout", BadStdout())

        # 不应抛出异常，被 except 捕获
        setup_encoding()

    def test_setup_encoding_buffer_false(self, monkeypatch):
        """测试 buffer 为 False（假值）"""
        monkeypatch.setattr(sys, "platform", "win32")

        class FalseBufferStdout:
            buffer = False

        monkeypatch.setattr(sys, "stdout", FalseBufferStdout())

        # 不应抛出异常
        setup_encoding()
