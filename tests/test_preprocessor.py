"""
测试: 文本预处理模块
基于 TDD - 先写测试
"""

import pytest
import sys
import os
import tempfile
from pathlib import Path

# 添加 src 到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from preprocessor import TextPreprocessor, preprocess_text


class TestPreprocessor:
    """文本预处理测试"""

    def setup_method(self):
        """每个测试方法前运行"""
        self.preprocessor = TextPreprocessor()

    def test_load_text_file(self):
        """测试加载文本文件"""
        # 创建临时文件
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", delete=False, suffix=".txt"
        ) as f:
            f.write("测试内容")
            temp_path = f.name

        try:
            content = self.preprocessor.load_text(temp_path)
            assert content == "测试内容"
        finally:
            os.unlink(temp_path)

    def test_load_text_file_not_found(self):
        """测试加载不存在的文件"""
        with pytest.raises(FileNotFoundError):
            self.preprocessor.load_text("不存在文件.txt")

    def test_encoding_detection_utf8(self):
        """测试 UTF-8 编码检测"""
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", delete=False, suffix=".txt"
        ) as f:
            f.write("UTF-8编码测试")
            temp_path = f.name

        try:
            content = self.preprocessor.load_text(temp_path)
            assert content == "UTF-8编码测试"
        finally:
            os.unlink(temp_path)

    def test_encoding_detection_gb18030(self):
        """测试 GB18030 编码检测"""
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="gb18030", delete=False, suffix=".txt"
        ) as f:
            f.write("GB18030编码测试")
            temp_path = f.name

        try:
            content = self.preprocessor.load_text(temp_path)
            assert content == "GB18030编码测试"
        finally:
            os.unlink(temp_path)

    def test_encoding_detection_gbk(self):
        """测试 GBK 编码检测"""
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="gbk", delete=False, suffix=".txt"
        ) as f:
            f.write("GBK编码测试")
            temp_path = f.name

        try:
            content = self.preprocessor.load_text(temp_path)
            assert content == "GBK编码测试"
        finally:
            os.unlink(temp_path)

    def test_text_normalization(self):
        """测试文本规范化"""
        # 测试 NFKC 规范化（全角转半角）
        text = "１００％"
        result = self.preprocessor.normalize(text)
        assert result == "100%"

    def test_text_normalization_fullwidth_space(self):
        """测试去除全角空格"""
        text = "测试　内容"
        result = self.preprocessor.normalize(text)
        assert result == "测试内容"

    def test_text_normalization_newline(self):
        """测试去除换行"""
        text = "测试\n\r内容"
        result = self.preprocessor.normalize(text)
        assert result == "测试内容"

    def test_sentence_split_chinese_punctuation(self):
        """测试中文标点分句"""
        text = "我国发射了卫星。它很先进。"
        result = self.preprocessor.split_sentences(text)
        assert result == ["我国发射了卫星", "它很先进"]

    def test_sentence_split_multiple_punctuations(self):
        """测试多种标点分句"""
        text = "第一句。第二句！第三句？第四句；第五句"
        result = self.preprocessor.split_sentences(text)
        assert result == ["第一句", "第二句", "第三句", "第四句", "第五句"]

    def test_sentence_split_english_punctuation(self):
        """测试英文标点分句"""
        text = "First sentence. Second sentence; Third sentence"
        result = self.preprocessor.split_sentences(text)
        assert result == ["First sentence", "Second sentence", "Third sentence"]

    def test_sentence_split_empty(self):
        """测试空文本处理"""
        result = self.preprocessor.split_sentences("")
        assert result == []

    def test_sentence_split_whitespace_only(self):
        """测试仅空白字符"""
        result = self.preprocessor.split_sentences("   ")
        assert result == []

    def test_sentence_split_no_punctuation(self):
        """测试无标点文本"""
        text = "这是没有标点的句子"
        result = self.preprocessor.split_sentences(text)
        assert result == ["这是没有标点的句子"]

    def test_process_full_pipeline(self):
        """测试完整处理流程"""
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", delete=False, suffix=".txt"
        ) as f:
            f.write("我国发射了卫星。它用于科学实验。")
            temp_path = f.name

        try:
            result = self.preprocessor.process(temp_path)
            assert len(result) == 2
            assert "我国发射了卫星" in result
            assert "它用于科学实验" in result
        finally:
            os.unlink(temp_path)

    def test_process_with_normalization(self):
        """测试处理时规范化"""
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", delete=False, suffix=".txt"
        ) as f:
            f.write("测试　内容。第一句。第二句")
            temp_path = f.name

        try:
            result = self.preprocessor.process(temp_path)
            # 全角空格应被去除
            assert "测试内容" in result[0]
        finally:
            os.unlink(temp_path)

    def test_convenience_function(self):
        """测试便捷函数"""
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", delete=False, suffix=".txt"
        ) as f:
            f.write("便捷函数测试。")
            temp_path = f.name

        try:
            result = preprocess_text(temp_path)
            assert len(result) >= 1
        finally:
            os.unlink(temp_path)
