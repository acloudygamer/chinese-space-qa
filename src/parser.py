"""
安全解析器模块
提供安全的 JSON/列表解析，替代 eval() 使用
"""

import json
import re
from typing import Any, List, Dict, Union


class SafeParser:
    """安全解析器"""

    @staticmethod
    def parse_list(content: str) -> List:
        """
        安全解析列表字符串

        Args:
            content: 列表内容字符串

        Returns:
            解析后的列表
        """
        if not content or not content.strip():
            return []

        # 尝试 JSON 解析
        try:
            result = json.loads(content)
            if isinstance(result, list):
                return result
            return [result]
        except (json.JSONDecodeError, TypeError):
            pass

        # 备用：正则提取（安全的替代方案）
        content = content.strip()

        # 处理单引号列表: ['a', 'b', 'c']
        if content.startswith("["):
            # 提取所有字符串
            items = re.findall(r"'([^']*)'", content)
            if items:
                return items

            # 提取数字
            numbers = re.findall(r"-?\d+\.?\d*", content)
            if numbers:
                try:
                    return [int(n) for n in numbers]
                except ValueError:
                    return [float(n) for n in numbers]

            # 空列表
            if content == "[]":
                return []

        return []

    @staticmethod
    def _convert_to_int(value: str) -> Any:
        """尝试将字符串转换为整数或浮点数"""
        try:
            return int(value)
        except ValueError:
            try:
                return float(value)
            except ValueError:
                return value

    @staticmethod
    def parse_dict(content: str) -> Dict:
        """
        安全解析字典字符串

        Args:
            content: 字典内容字符串

        Returns:
            解析后的字典
        """
        if not content or not content.strip():
            return {}

        # 尝试 JSON 解析（支持双引号）
        try:
            result = json.loads(content)
            if isinstance(result, dict):
                return result
            return {}
        except (json.JSONDecodeError, TypeError):
            pass

        # 尝试将单引号替换为双引号后解析
        try:
            # 替换单引号为双引号（但要小心处理内部的单引号）
            normalized = content.replace("'", '"')
            result = json.loads(normalized)
            if isinstance(result, dict):
                return result
            return {}
        except (json.JSONDecodeError, TypeError):
            pass

        # 备用：正则提取（处理 {'key': value} 格式）- 简化版
        content = content.strip()
        if content.startswith("{"):
            # 提取键值对，处理嵌套列表
            result = {}

            # 匹配 'key': [...] 或 'key': value
            # 先匹配列表值
            list_pattern = r"'([^']+)':\s*(\[[^\]]+\])"
            for match in re.finditer(list_pattern, content):
                key = match.group(1)
                value_str = match.group(2)
                # 尝试解析列表
                try:
                    # 将单引号替换为双引号
                    value_str = value_str.replace("'", '"')
                    value = json.loads(value_str)
                    result[key] = value
                except:
                    result[key] = value_str

            # 再匹配简单值
            simple_pattern = r"'([^']+)':\s*'([^']*)'"
            for match in re.finditer(simple_pattern, content):
                key = match.group(1)
                value = match.group(2)
                if key not in result:
                    result[key] = value

            return result

        return {}

    @staticmethod
    def parse_list_of_lists(content: str) -> List[List]:
        """
        安全解析嵌套列表字符串（用于分词结果）

        Args:
            content: 嵌套列表内容字符串

        Returns:
            解析后的嵌套列表
        """
        if not content or not content.strip():
            return []

        # 尝试 JSON 解析
        try:
            result = json.loads(content)
            if isinstance(result, list):
                # 如果是单层列表包装成双层
                if result and not isinstance(result[0], list):
                    return [result]
                return result
            return []
        except (json.JSONDecodeError, TypeError):
            pass

        # 备用：正则提取
        content = content.strip()

        # 处理 [[...]] 格式
        match = re.search(r"\[\[(.*?)\]\]", content)
        if match:
            inner = match.group(1)
            # 提取字符串
            items = re.findall(r"'([^']*)'", inner)
            if items:
                return [items]

        # 处理 [...] 格式
        if content.startswith("["):
            items = re.findall(r"'([^']*)'", content)
            if items:
                return [items]

        return []


# 便捷函数
def safe_parse_list(content: str) -> List:
    """安全解析列表"""
    return SafeParser.parse_list(content)


def safe_parse_dict(content: str) -> Dict:
    """安全解析字典"""
    return SafeParser.parse_dict(content)


def safe_parse_list_of_lists(content: str) -> List[List]:
    """安全解析嵌套列表"""
    return SafeParser.parse_list_of_lists(content)
