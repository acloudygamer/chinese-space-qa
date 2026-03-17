"""
测试: 知识图谱模块
基于 TDD - 先写测试
"""

import pytest
import sys
import os
import tempfile

# 添加 src 到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from knowledge_graph import KnowledgeGraph, build_knowledge_graph


class MockNERExtractor:
    """模拟 NER 提取器"""

    def __init__(self, entities):
        self._entities = entities

    def extract_entities(self):
        return self._entities


class MockRelationExtractor:
    """模拟关系提取器"""

    def __init__(self, relations):
        self._relations = relations

    def extract_relations(self):
        return self._relations


class TestKnowledgeGraph:
    """知识图谱测试"""

    def setup_method(self):
        """每个测试方法前运行"""
        self.kg = KnowledgeGraph()

    def test_add_entity(self):
        """测试添加实体"""
        self.kg.add_entity("澳门", "地名")
        assert "澳门" in self.kg.entities
        assert self.kg.entity_types["澳门"] == "地名"

    def test_add_duplicate_entity(self):
        """测试添加重复实体"""
        self.kg.add_entity("澳门", "地名")
        self.kg.add_entity("澳门", "地名")
        assert len(self.kg.entities) == 1

    def test_add_relation(self):
        """测试添加关系"""
        self.kg.add_entity("澳门", "地名")
        self.kg.add_entity("卫星", "机构名")
        self.kg.add_relation("澳门", "发射", "卫星")
        assert len(self.kg.relations) == 1
        assert ("澳门", "发射", "卫星") in self.kg.relations

    def test_entity_relations(self):
        """测试实体关系存储"""
        self.kg.add_entity("澳门", "地名")
        self.kg.add_entity("卫星", "机构名")
        self.kg.add_relation("澳门", "发射", "卫星")
        assert len(self.kg.entity_relations["澳门"]) > 0

    def test_reverse_relation(self):
        """测试反向关系"""
        self.kg.add_entity("实体A", "类型1")
        self.kg.add_entity("实体B", "类型2")
        self.kg.add_relation("实体A", "关系1", "实体B")
        # 应包含反向关系
        assert any("反向_关系1" in rel[0] for rel in self.kg.entity_relations["实体B"])

    def test_get_entity_info(self):
        """测试获取实体信息"""
        self.kg.add_entity("澳门", "地名")
        self.kg.add_entity("卫星", "机构名")
        self.kg.add_relation("澳门", "发射", "卫星")
        info = self.kg.get_entity_info("澳门")
        assert info["name"] == "澳门"
        assert info["type"] == "地名"
        assert len(info["relations"]) > 0

    def test_get_entity_info_not_exist(self):
        """测试获取不存在实体的信息"""
        info = self.kg.get_entity_info("不存在")
        assert info["name"] == "不存在"
        assert info["type"] == "未知"
        assert info["relations"] == []

    def test_query_with_relation_type(self):
        """测试按关系类型查询"""
        self.kg.add_entity("澳门", "地名")
        self.kg.add_entity("卫星", "机构名")
        self.kg.add_relation("澳门", "发射", "卫星")
        results = self.kg.query("澳门", "发射")
        assert "卫星" in results

    def test_query_without_relation_type(self):
        """测试不指定关系类型查询"""
        self.kg.add_entity("澳门", "地名")
        self.kg.add_entity("卫星1", "机构名")
        self.kg.add_entity("卫星2", "机构名")
        self.kg.add_relation("澳门", "发射", "卫星1")
        self.kg.add_relation("澳门", "拥有", "卫星2")
        results = self.kg.query("澳门")
        assert len(results) == 2

    def test_to_dict(self):
        """测试导出为字典"""
        self.kg.add_entity("澳门", "地名")
        self.kg.add_entity("卫星", "机构名")
        self.kg.add_relation("澳门", "发射", "卫星")
        d = self.kg.to_dict()
        assert "entities" in d
        assert "relations" in d
        assert len(d["entities"]) == 2

    def test_to_neo4j_format(self):
        """测试导出为 Neo4j 格式"""
        self.kg.add_entity("澳门", "地名")
        self.kg.add_entity("卫星", "机构名")
        self.kg.add_relation("澳门", "发射", "卫星")
        neo4j_data = self.kg.to_neo4j_format()
        assert "nodes" in neo4j_data
        assert "edges" in neo4j_data

    def test_to_graphviz(self):
        """测试导出为 Graphviz 格式"""
        self.kg.add_entity("澳门", "地名")
        self.kg.add_entity("卫星", "机构名")
        self.kg.add_relation("澳门", "发射", "卫星")
        dot = self.kg.to_graphviz()
        assert "digraph" in dot
        assert "澳门" in dot

    def test_build_from_extractors(self):
        """测试从提取器构建图谱"""
        ner_extractor = MockNERExtractor(
            [
                {"word": "澳门", "type": "地名", "type_code": "Ns", "sent_idx": 0},
                {"word": "卫星", "type": "机构名", "type_code": "Ni", "sent_idx": 0},
            ]
        )
        rel_extractor = MockRelationExtractor(
            [
                {
                    "head_word": "澳门",
                    "child_word": "卫星",
                    "relation": "发射",
                    "relation_code": "VOB",
                    "sent_idx": 0,
                }
            ]
        )
        kg = KnowledgeGraph()
        kg.build_from_extractors(ner_extractor, rel_extractor)
        assert len(kg.entities) >= 2
        assert len(kg.relations) >= 1

    def test_build_from_extractors_with_unknown_entity(self):
        """测试构建时添加未知实体"""
        ner_extractor = MockNERExtractor(
            [
                {"word": "澳门", "type": "地名", "type_code": "Ns", "sent_idx": 0},
            ]
        )
        rel_extractor = MockRelationExtractor(
            [
                {
                    "head_word": "澳门",
                    "child_word": "发射中心",
                    "relation": "位于",
                    "relation_code": "POB",
                    "sent_idx": 0,
                }
            ]
        )
        kg = KnowledgeGraph()
        kg.build_from_extractors(ner_extractor, rel_extractor)
        # 发射中心应为未知类型
        assert "发射中心" in kg.entities
        assert kg.entity_types.get("发射中心") == "未知"

    def test_convenience_function(self):
        """测试便捷函数（需要文件）"""
        # 此测试需要实际文件，仅验证函数存在
        assert callable(build_knowledge_graph)
