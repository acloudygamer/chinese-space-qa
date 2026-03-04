"""
测试: 文本预处理模块
基于 TDD - 先写测试
"""

import pytest
import sys
import os

# 添加 src 到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))


class TestPreprocessor:
    """文本预处理测试"""

    def test_load_text_file(self):
        """测试加载文本文件"""
        # TODO: 实现文件加载
        pass

    def test_encoding_detection(self):
        """测试编码自动识别 (gb18030/utf-8)"""
        # TODO: 实现编码检测
        pass

    def test_text_normalization(self):
        """测试文本规范化"""
        # TODO: 实现 NFKC 规范化
        pass

    def test_sentence_split(self):
        """测试分句"""
        # TODO: 实现按标点分句
        pass

    def test_sentence_split_chinese_punctuation(self):
        """测试中文标点分句"""
        # 输入: "我国发射了卫星。它很先进。"
        # 期望: ["我国发射了卫星", "它很先进"]
        pass

    def test_empty_text_handling(self):
        """测试空文本处理"""
        # 应返回空列表
        pass
