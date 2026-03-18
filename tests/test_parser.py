"""
测试: 安全解析器模块
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from parser import SafeParser, safe_parse_list, safe_parse_dict, safe_parse_list_of_lists


class TestSafeParser:
    """SafeParser 测试"""

    def test_parse_list_json_format(self):
        """测试 JSON 格式列表解析"""
        result = SafeParser.parse_list('["a", "b", "c"]')
        assert result == ["a", "b", "c"]

    def test_parse_list_single_quote(self):
        """测试单引号列表解析"""
        result = SafeParser.parse_list("['a', 'b', 'c']")
        assert result == ["a", "b", "c"]

    def test_parse_list_numbers(self):
        """测试数字列表解析"""
        result = SafeParser.parse_list("[1, 2, 3]")
        assert result == [1, 2, 3]

    def test_parse_list_floats(self):
        """测试浮点数列表"""
        result = SafeParser.parse_list("[1.5, 2.5, 3.5]")
        assert result == [1.5, 2.5, 3.5]

    def test_parse_list_negative_numbers(self):
        """测试负数列表"""
        result = SafeParser.parse_list("[-1, -2, -3]")
        assert result == [-1, -2, -3]

    def test_parse_list_empty(self):
        """测试空字符串"""
        result = SafeParser.parse_list("")
        assert result == []

    def test_parse_list_whitespace(self):
        """测试纯空白"""
        result = SafeParser.parse_list("   ")
        assert result == []

    def test_parse_list_empty_brackets(self):
        """测试空列表字符串"""
        result = SafeParser.parse_list("[]")
        assert result == []

    def test_parse_list_not_a_list(self):
        """测试非列表 JSON（应返回包装后的列表）"""
        result = SafeParser.parse_list('"single"')
        assert result == ["single"]

    def test_parse_list_invalid(self):
        """测试无效输入"""
        result = SafeParser.parse_list("{invalid}")
        assert result == []

    def test_convert_to_int(self):
        """测试 _convert_to_int"""
        assert SafeParser._convert_to_int("42") == 42
        assert SafeParser._convert_to_int("3.14") == 3.14
        assert SafeParser._convert_to_int("abc") == "abc"

    def test_parse_dict_json_format(self):
        """测试 JSON 格式字典解析"""
        result = SafeParser.parse_dict('{"key": "value", "num": 123}')
        assert result["key"] == "value"
        assert result["num"] == 123

    def test_parse_dict_single_quote(self):
        """测试单引号字典解析"""
        result = SafeParser.parse_dict("{'key': 'value'}")
        assert result["key"] == "value"

    def test_parse_dict_single_quote_with_list(self):
        """测试含列表值的字典"""
        result = SafeParser.parse_dict("{'head': [1, 2], 'label': ['a']}")
        assert result["head"] == [1, 2]
        assert result["label"] == ["a"]

    def test_parse_dict_empty(self):
        """测试空字典"""
        result = SafeParser.parse_dict("")
        assert result == {}

    def test_parse_dict_whitespace(self):
        """测试空白输入"""
        result = SafeParser.parse_dict("   ")
        assert result == {}

    def test_parse_dict_not_a_dict(self):
        """测试非字典 JSON"""
        result = SafeParser.parse_dict('[1, 2, 3]')
        assert result == {}

    def test_parse_dict_regex_fallback(self):
        """测试正则备用路径"""
        result = SafeParser.parse_dict("{'key1': 'val1', 'key2': 'val2'}")
        assert "key1" in result or "key2" in result

    def test_parse_dict_with_nested_list(self):
        """测试含嵌套列表的字典"""
        result = SafeParser.parse_dict("{'data': [1, 2, 3]}")
        assert result.get("data") == [1, 2, 3]

    def test_parse_list_of_lists_json(self):
        """测试 JSON 嵌套列表解析"""
        result = SafeParser.parse_list_of_lists('[["a", "b"], ["c"]]')
        assert result == [["a", "b"], ["c"]]

    def test_parse_list_of_lists_single_layer(self):
        """测试单层列表包装"""
        result = SafeParser.parse_list_of_lists('["a", "b"]')
        assert result == [["a", "b"]]

    def test_parse_list_of_lists_empty(self):
        """测试空输入"""
        result = SafeParser.parse_list_of_lists("")
        assert result == []

    def test_parse_list_of_lists_whitespace(self):
        """测试空白输入"""
        result = SafeParser.parse_list_of_lists("   ")
        assert result == []

    def test_parse_list_of_lists_single_quote(self):
        """测试单引号嵌套列表（备用路径，只处理单层）"""
        # 正则备用路径无法处理多层嵌套，此处测试单层单引号
        result = SafeParser.parse_list_of_lists("['a', 'b']")
        assert result == [["a", "b"]]

    def test_parse_list_of_lists_regex_fallback(self):
        """测试正则备用路径"""
        # 测试单层嵌套格式
        result = SafeParser.parse_list_of_lists("[['测试1', '测试2']]")
        assert result == [["测试1", "测试2"]]

    def test_safe_parse_list_function(self):
        """测试便捷函数 safe_parse_list"""
        result = safe_parse_list("['x', 'y']")
        assert result == ["x", "y"]

    def test_safe_parse_dict_function(self):
        """测试便捷函数 safe_parse_dict"""
        result = safe_parse_dict('{"a": 1}')
        assert result["a"] == 1

    def test_safe_parse_list_of_lists_function(self):
        """测试便捷函数 safe_parse_list_of_lists"""
        result = safe_parse_list_of_lists('[["p"]]')
        assert result == [["p"]]

    def test_parse_list_mixed_quotes(self):
        """测试混合引号"""
        result = SafeParser.parse_list('["hello", "world"]')
        assert result == ["hello", "world"]

    def test_parse_dict_numbers_only(self):
        """测试纯数字字典"""
        result = SafeParser.parse_dict('{"a": 1, "b": 2}')
        assert result["a"] == 1
        assert result["b"] == 2

    def test_parse_dict_boolean_values(self):
        """测试布尔值字典"""
        result = SafeParser.parse_dict('{"a": true, "b": false}')
        assert result["a"] is True
        assert result["b"] is False

    def test_parse_dict_none_value(self):
        """测试 None 值字典"""
        result = SafeParser.parse_dict('{"a": null}')
        assert result["a"] is None
