"""
文本预处理模块
负责加载、规范化、分句
"""

import unicodedata
import re
from pathlib import Path
from typing import List, Optional


class TextPreprocessor:
    """文本预处理器"""

    def __init__(self):
        self.supported_encodings = ["utf-8", "gb18030", "gbk", "gb2312"]

    def load_text(self, file_path: str) -> str:
        """
        加载文本文件，自动检测编码

        Args:
            file_path: 文件路径

        Returns:
            文件内容字符串
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"文件未找到: {file_path}")

        # 尝试多种编码
        for encoding in self.supported_encodings:
            try:
                with open(path, "r", encoding=encoding) as f:
                    return f.read()
            except UnicodeDecodeError:
                continue

        raise ValueError(f"无法解码文件: {file_path}")

    def normalize(self, text: str) -> str:
        """
        文本规范化

        - NFKC 规范化
        - 去除全角空格

        Args:
            text: 原始文本

        Returns:
            规范化后的文本
        """
        # NFKC 规范化
        text = unicodedata.normalize("NFKC", text)
        # 去除全角空格
        text = text.replace(" ", "")
        # 去除换行
        text = text.replace("\n", "").replace("\r", "")
        return text

    def split_sentences(self, text: str) -> List[str]:
        """
        句子分割

        按中文标点分割: 。 ！ ？ ；
        按英文标点分割: . ! ? ; ,

        Args:
            text: 文本

        Returns:
            句子列表
        """
        # 按标点分割
        pattern = r"[。！？；,.;:：]"
        sentences = re.split(pattern, text)

        # 去除空字符串和空白
        sentences = [s.strip() for s in sentences if s.strip()]

        return sentences

    def process(self, file_path: str) -> List[str]:
        """
        完整处理流程

        Args:
            file_path: 输入文件路径

        Returns:
            处理后的句子列表
        """
        # 加载
        text = self.load_text(file_path)

        # 规范化
        text = self.normalize(text)

        # 分句
        sentences = self.split_sentences(text)

        return sentences


# 便捷函数
def preprocess_text(file_path: str) -> List[str]:
    """
    预处理文本文件

    Args:
        file_path: 文本文件路径

    Returns:
        句子列表
    """
    preprocessor = TextPreprocessor()
    return preprocessor.process(file_path)


if __name__ == "__main__":
    # 测试
    preprocessor = TextPreprocessor()
    sentences = preprocessor.process(r"..\自然语言处理实验2-实验数据.txt")
    for i, sent in enumerate(sentences):
        print(f"{i + 1}. {sent}")
