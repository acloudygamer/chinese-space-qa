"""
测试: 关系抽取模块
基于 TDD - 先写测试
"""

import pytest
import sys
import os
import tempfile
import json

# 添加 src 到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from relation import RelationExtractor, extract_relations


class TestRelationExtractor:
    """关系抽取测试"""

    def setup_method(self):
        """每个测试方法前运行"""
        self.temp_file = tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", delete=False, suffix=".txt"
        )
        self.temp_path = self.temp_file.name

    def teardown_method(self):
        """每个测试方法后运行"""
        import time

        try:
            # Windows 上文件可能仍被占用，等待后重试
            for _ in range(3):
                try:
                    os.unlink(self.temp_path)
                    break
                except PermissionError:
                    time.sleep(0.1)
        except FileNotFoundError:
            pass

    def _write_ltp_results(self, content: str):
        """写入 LTP 结果"""
        with open(self.temp_path, "w", encoding="utf-8") as f:
            f.write(content)

    def test_parse_dependency(self):
        """测试解析依存分析结果"""
        self._write_ltp_results("""分词结果：['澳门', '科学', '一号', '卫星', '发射']
依存句法分析结果：{'head': [5, 3, 4, 5, 0], 'label': ['ATT', 'ATT', 'SBV', 'VOB', 'HED']}
""")
        extractor = RelationExtractor(self.temp_path)
        results = extractor.parse_dependency()
        assert len(results) == 1

    def test_file_not_found(self):
        """测试文件不存在"""
        with pytest.raises(FileNotFoundError):
            extractor = RelationExtractor("不存在的文件.txt")
            extractor.parse_dependency()

    def test_extract_sbv_relation(self):
        """测试提取主谓关系"""
        self._write_ltp_results("""分词结果：['卫星', '发射']
依存句法分析结果：{'head': [2, 0], 'label': ['SBV', 'HED']}
""")
        extractor = RelationExtractor(self.temp_path)
        relations = extractor.extract_relations()
        assert len(relations) > 0

    def test_extract_vob_relation(self):
        """测试提取动宾关系"""
        self._write_ltp_results("""分词结果：['发射', '卫星']
依存句法分析结果：{'head': [1, 0], 'label': ['HED', 'VOB']}
""")
        extractor = RelationExtractor(self.temp_path)
        relations = extractor.extract_relations()
        assert len(relations) > 0
        assert any(r["relation"] == "动宾关系" for r in relations)

    def test_exclude_core_relation(self):
        """测试排除核心关系"""
        self._write_ltp_results("""分词结果：['发射', '卫星']
依存句法分析结果：{'head': [1, 0], 'label': ['HED', 'VOB']}
""")
        extractor = RelationExtractor(self.temp_path)
        relations = extractor.extract_relations(include_core=False)
        # HED 关系应被排除
        assert not any(r["relation_code"] == "HED" for r in relations)

    def test_include_core_relation(self):
        """测试包含核心关系"""
        self._write_ltp_results("""分词结果：['发射', '卫星']
依存句法分析结果：{'head': [1, 0], 'label': ['HED', 'VOB']}
""")
        extractor = RelationExtractor(self.temp_path)
        relations = extractor.extract_relations(include_core=True)
        assert any(r["relation_code"] == "HED" for r in relations)

    def test_relation_label_mapping(self):
        """测试关系标签映射"""
        self._write_ltp_results("""分词结果：['国家', '航天局']
依存句法分析结果：{'head': [2, 0], 'label': ['ATT', 'HED']}
""")
        extractor = RelationExtractor(self.temp_path)
        relations = extractor.extract_relations()
        assert any(r["relation"] == "定中关系" for r in relations)

    def test_get_entity_relations(self):
        """测试获取实体间关系"""
        self._write_ltp_results("""分词结果：['澳门', '科学', '一号', '卫星']
词性标注结果：['ns', 'n', 'm', 'n']
命名实体识别结果：[('Ns', '澳门')]

分词结果：['澳门', '发射', '卫星']
依存句法分析结果：{'head': [3, 3, 0], 'label': ['SBV', 'ADV', 'HED']}
""")
        extractor = RelationExtractor(self.temp_path)
        entities = [{"word": "澳门", "type": "地名"}]
        entity_relations = extractor.get_entity_relations(entities)
        # 关系中应包含 '澳门'
        assert any(
            r["head_word"] == "澳门" or r["child_word"] == "澳门"
            for r in entity_relations
        )

    def test_parse_json_format(self):
        """测试 JSON 格式解析"""
        self._write_ltp_results("""分词结果：["测试", "内容"]
依存句法分析结果：{"head": [2, 0], "label": ["ATT", "HED"]}
""")
        extractor = RelationExtractor(self.temp_path)
        results = extractor.parse_dependency()
        assert len(results) > 0

    def test_parse_list_format(self):
        """测试列表格式解析"""
        self._write_ltp_results("""分词结果：['测试', '内容']
依存句法分析结果：[[3, 1, 2]]
""")
        extractor = RelationExtractor(self.temp_path)
        # 不应崩溃，返回空结果或部分结果
        results = extractor.parse_dependency()
        assert isinstance(results, list)

    def test_empty_dependency(self):
        """测试空依存分析"""
        self._write_ltp_results("""分词结果：['测试']
依存句法分析结果：{}
""")
        extractor = RelationExtractor(self.temp_path)
        relations = extractor.extract_relations()
        # 应返回空列表
        assert isinstance(relations, list)

    def test_convenience_function(self):
        """测试便捷函数"""
        self._write_ltp_results("""分词结果：['测试']
依存句法分析结果：{'head': [0], 'label': ['HED']}
""")
        result = extract_relations(self.temp_path)
        assert isinstance(result, list)

    def test_multiple_sentences(self):
        """测试多句处理"""
        self._write_ltp_results("""分词结果：['第一句']
依存句法分析结果：{'head': [0], 'label': ['HED']}

分词结果：['第二句']
依存句法分析结果：{'head': [0], 'label': ['HED']}
""")
        extractor = RelationExtractor(self.temp_path)
        results = extractor.parse_dependency()
        assert len(results) == 2
