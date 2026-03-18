"""
测试: QA 引擎模块
"""

import pytest
import sys
import os
import tempfile
import json

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from qa_engine import QAEngine


class MockNERExtractor:
    def extract_entities(self):
        return [
            {"word": "澳门", "type": "地名", "type_code": "Ns", "sent_idx": 0},
            {"word": "卫星", "type": "机构名", "type_code": "Ni", "sent_idx": 0},
            {"word": "2023年", "type": "时间", "type_code": "Nt", "sent_idx": 0},
        ]


class MockRelationExtractor:
    def extract_relations(self):
        return [
            {
                "head_word": "澳门",
                "child_word": "发射",
                "relation": "VOB",
                "relation_code": "VOB",
                "sent_idx": 0,
            }
        ]


class TestQAEngine:
    """QA 引擎测试"""

    def setup_method(self):
        # 创建临时 KG 文件，避免加载实际文件
        self.temp_kg = tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", delete=False, suffix=".json"
        )
        kg_data = {
            "entities": [
                {"name": "澳门", "type": "地名"},
                {"name": "卫星", "type": "机构名"},
                {"name": "2023年", "type": "时间"},
            ],
            "relations": [
                {"head": "澳门", "relation": "发射", "tail": "卫星"},
            ],
        }
        json.dump(kg_data, self.temp_kg, ensure_ascii=False)
        self.temp_kg.close()
        self.qa = QAEngine(self.temp_kg.name)

    def teardown_method(self):
        import time

        try:
            for _ in range(3):
                try:
                    os.unlink(self.temp_kg.name)
                    break
                except PermissionError:
                    time.sleep(0.1)
        except FileNotFoundError:
            pass

    def test_classify_who_launch(self):
        """测试 '谁发射' 问题分类"""
        qtype, params = self.qa._classify_question("谁发射了卫星？")
        assert qtype == "who_launch"

    def test_classify_when_launch(self):
        """测试 '什么时候发射' 问题分类"""
        qtype, params = self.qa._classify_question("什么时候发射的？")
        assert qtype == "when_launch"

    def test_classify_where_launch(self):
        """测试 '在哪里发射' 问题分类"""
        qtype, params = self.qa._classify_question("在哪里发射？")
        assert qtype == "where_launch"

    def test_classify_what_satellite(self):
        """测试 '什么卫星' 问题分类"""
        qtype, params = self.qa._classify_question("什么卫星？")
        assert qtype == "what_satellite"

    def test_classify_cooperation(self):
        """测试 '合作' 问题分类"""
        qtype, params = self.qa._classify_question("澳门和中国合作了吗？")
        assert qtype == "cooperation"

    def test_classify_significance(self):
        """测试 '意义' 问题分类（需要含 '的' 字）"""
        qtype, params = self.qa._classify_question("有什么样的意义？")
        assert qtype == "significance"

    def test_classify_significance_without_de(self):
        """测试不含 '的' 的意义问题归为通用"""
        # "什么意义" 没有 "的" 字，不匹配模式，应归为 general
        qtype, params = self.qa._classify_question("什么意义？")
        assert qtype == "general"

    def test_classify_general(self):
        """测试通用问题分类"""
        qtype, params = self.qa._classify_question("你好")
        assert qtype == "general"

    def test_answer_when_launch(self):
        """测试时间问题回答"""
        result = self.qa._answer_when_launch("什么时候发射？")
        assert isinstance(result, str)

    def test_answer_where_launch(self):
        """测试地点问题回答"""
        result = self.qa._answer_where_launch("在哪里发射？")
        assert isinstance(result, str)

    def test_answer_what_satellite(self):
        """测试卫星问题回答"""
        result = self.qa._answer_what_satellite("什么卫星？")
        assert isinstance(result, str)

    def test_answer_cooperation(self):
        """测试合作问题回答"""
        result = self.qa._answer_cooperation("合作情况？")
        assert isinstance(result, str)

    def test_answer_significance(self):
        """测试意义问题回答"""
        result = self.qa._answer_significance("意义？")
        assert "意义" in result

    def test_answer_general(self):
        """测试通用问答"""
        result = self.qa._answer_general("你好")
        assert isinstance(result, str)

    def test_find_entity(self):
        """测试实体查找"""
        entity = self.qa._find_entity("澳门")
        assert entity is not None
        assert entity["name"] == "澳门"

    def test_find_entity_fuzzy(self):
        """测试模糊实体查找"""
        entity = self.qa._find_entity("澳")
        assert entity is not None

    def test_find_entity_not_found(self):
        """测试不存在的实体"""
        entity = self.qa._find_entity("不存在的实体")
        assert entity is None

    def test_find_relations(self):
        """测试关系查找"""
        rels = self.qa._find_relations("澳门")
        assert isinstance(rels, list)

    def test_answer_integration(self):
        """测试完整问答"""
        result = self.qa.answer("什么时候发射？")
        assert isinstance(result, str)
        assert len(result) > 0

    def test_kg_data_loaded(self):
        """测试知识图谱加载"""
        assert self.qa.kg_data is not None
        assert "entities" in self.qa.kg_data

    def test_question_with_extra_whitespace(self):
        """测试带空白的问句"""
        qtype, params = self.qa._classify_question("  谁发射了卫星？  ")
        assert qtype == "who_launch"

    def test_answer_with_no_entities(self):
        """测试空知识图谱的回答"""
        temp_kg = tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", delete=False, suffix=".json"
        )
        json.dump({"entities": [], "relations": []}, temp_kg, ensure_ascii=False)
        temp_kg.close()

        try:
            qa = QAEngine(temp_kg.name)
            result = qa._answer_when_launch("什么时候发射？")
            assert isinstance(result, str)
        finally:
            import time

            try:
                for _ in range(3):
                    try:
                        os.unlink(temp_kg.name)
                        break
                    except PermissionError:
                        time.sleep(0.1)
            except FileNotFoundError:
                pass

    def test_find_relations_not_found(self):
        """测试查找不存在实体的关系"""
        rels = self.qa._find_relations("不存在的实体")
        assert rels == []

    def test_classify_complex_question(self):
        """测试复杂问题分类"""
        qtype, _ = self.qa._classify_question("澳门科学一号是什么时候发射的？")
        assert qtype == "when_launch"

    def test_answer_cooperation_no_relation(self):
        """测试无合作关系时的回答"""
        # 创建没有合作关系的 KG
        temp_kg = tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", delete=False, suffix=".json"
        )
        json.dump(
            {
                "entities": [{"name": "A地区", "type": "地名"}],
                "relations": [{"head": "A地区", "relation": "位于", "tail": "B地"}],
            },
            temp_kg,
            ensure_ascii=False,
        )
        temp_kg.close()

        try:
            qa = QAEngine(temp_kg.name)
            result = qa._answer_cooperation("合作情况？")
            assert isinstance(result, str)
            assert "澳门" in result  # 默认回答会提到澳门
        finally:
            import time

            try:
                for _ in range(3):
                    try:
                        os.unlink(temp_kg.name)
                        break
                    except PermissionError:
                        time.sleep(0.1)
            except FileNotFoundError:
                pass

    def test_answer_general_with_matching_keyword(self):
        """测试通用问答匹配关键词"""
        result = self.qa._answer_general("澳门的情况？")
        assert isinstance(result, str)
