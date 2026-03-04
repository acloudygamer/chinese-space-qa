"""
测试: NER 实体识别模块
基于 TDD - 先写测试
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))


class TestNERExtractor:
    """NER 实体识别测试"""

    def test_load_ltp_model(self):
        """测试加载 LTP 模型"""
        # TODO: 加载 small1 模型
        pass

    def test_recognize_person(self):
        """测试识别人名"""
        # 输入: "张三是工程师"
        # 期望: [("张三", "Nh", 0, 2)]
        pass

    def test_recognize_location(self):
        """测试识别地名"""
        # 输入: "澳门发射了卫星"
        # 期望: [("澳门", "Ns", 0, 2)]
        pass

    def test_recognize_organization(self):
        """测试识别机构名"""
        # 输入: "国家航天局"
        # 期望: [("国家航天局", "Ni", 0, 4)]
        pass

    def test_recognize_multiple_entities(self):
        """测试识别多个实体"""
        # 输入: "国家航天局与澳门合作"
        # 期望: 多个实体
        pass

    def test_empty_sentence(self):
        """测试空句子处理"""
        # 应返回空列表
        pass
