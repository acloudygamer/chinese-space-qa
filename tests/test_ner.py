"""
测试: NER 实体识别模块
基于 TDD - 先写测试
"""

import pytest
import sys
import os
import tempfile

# 添加 src 到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from ner import NERExtractor, extract_entities

class TestNERExtractor:
    """NER 实体识别测试"""

    def setup_method(self):
        """每个测试方法前运行"""
        # 创建临时测试文件
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

    def test_load_ltp_results(self):
        """测试加载 LTP 结果文件"""
        self._write_ltp_results("""分词结果：['澳门', '科学', '一号', '卫星']
词性标注结果：['ns', 'n', 'm', 'n']
命名实体识别结果：[('Ns', '澳门')]
""")
        extractor = NERExtractor(self.temp_path)
        results = extractor.parse_results()
        assert len(results) == 1

    def test_file_not_found(self):
        """测试文件不存在"""
        with pytest.raises(FileNotFoundError):
            extractor = NERExtractor("不存在的文件.txt")
            extractor.parse_results()

    def test_recognize_location(self):
        """测试识别地名"""
        self._write_ltp_results("""分词结果：['澳门', '发射', '了', '卫星']
词性标注结果：['ns', 'v', 'u', 'n']
命名实体识别结果：[('Ns', '澳门')]
""")
        extractor = NERExtractor(self.temp_path)
        entities = extractor.extract_entities()
        assert len(entities) > 0
        assert any(e["word"] == "澳门" for e in entities)

    def test_recognize_person(self):
        """测试识别人名"""
        self._write_ltp_results("""分词结果：['张', '三', '是', '工程师']
词性标注结果：['nh', 'n', 'v', 'n']
命名实体识别结果：[('Nh', '张三')]
""")
        extractor = NERExtractor(self.temp_path)
        entities = extractor.extract_entities()
        assert len(entities) > 0
        assert any(e["word"] == "张三" for e in entities)

    def test_recognize_organization(self):
        """测试识别机构名"""
        self._write_ltp_results("""分词结果：['国家', '航天局', '发布', '消息']
词性标注结果：['n', 'ni', 'v', 'n']
命名实体识别结果：[('Ni', '国家航天局')]
""")
        extractor = NERExtractor(self.temp_path)
        entities = extractor.extract_entities()
        assert len(entities) > 0
        assert any(e["word"] == "国家航天局" for e in entities)

    def test_recognize_time(self):
        """测试识别时间"""
        self._write_ltp_results("""分词结果：['昨天', '发射', '了', '卫星']
词性标注结果：['nt', 'v', 'u', 'n']
命名实体识别结果：[('Nt', '昨天')]
""")
        extractor = NERExtractor(self.temp_path)
        entities = extractor.extract_entities()
        assert len(entities) > 0
        assert any(e["word"] == "昨天" for e in entities)

    def test_recognize_multiple_entities(self):
        """测试识别多个实体"""
        self._write_ltp_results("""分词结果：['国家', '航天局', '与', '澳门', '合作']
词性标注结果：['n', 'ni', 'p', 'ns', 'v']
命名实体识别结果：[('Ni', '国家航天局'), ('Ns', '澳门')]
""")
        extractor = NERExtractor(self.temp_path)
        entities = extractor.extract_entities()
        assert len(entities) == 2

    def test_empty_ner_content(self):
        """测试无实体情况"""
        self._write_ltp_results("""分词结果：['今天', '天气', '好']
词性标注结果：['nt', 'n', 'a']
命名实体识别结果：[]
""")
        extractor = NERExtractor(self.temp_path)
        entities = extractor.extract_entities()
        assert len(entities) == 0

    def test_get_unique_entities(self):
        """测试获取唯一实体"""
        self._write_ltp_results("""分词结果：['澳门', '发射', '卫星']
词性标注结果：['ns', 'v', 'n']
命名实体识别结果：[('Ns', '澳门')]

分词结果：['澳门', '科学', '一号']
词性标注结果：['ns', 'n', 'm']
命名实体识别结果：[('Ns', '澳门')]
""")
        extractor = NERExtractor(self.temp_path)
        entities = extractor.extract_entities()
        unique = extractor.get_unique_entities(entities)
        assert "地名" in unique
        assert "澳门" in unique["地名"]

    def test_entity_type_mapping(self):
        """测试实体类型映射"""
        self._write_ltp_results("""分词结果：['张三']
词性标注结果：['nh']
命名实体识别结果：[('Nh', '张三')]
""")
        extractor = NERExtractor(self.temp_path)
        entities = extractor.extract_entities()
        assert entities[0]["type"] == "人名"
        assert entities[0]["type_code"] == "Nh"

    def test_entity_sentence_index(self):
        """测试实体句子索引"""
        self._write_ltp_results("""分词结果：['澳门']
词性标注结果：['ns']
命名实体识别结果：[('Ns', '澳门')]

分词结果：['北京']
词性标注结果：['ns']
命名实体识别结果：[('Ns', '北京')]
""")
        extractor = NERExtractor(self.temp_path)
        entities = extractor.extract_entities()
        # 第一个实体的索引应该是 0
        assert entities[0]["sent_idx"] == 0

    def test_parse_list_json_format(self):
        """测试 JSON 格式列表解析"""
        self._write_ltp_results("""分词结果：["澳门", "科学", "一号"]
词性标注结果：["ns", "n", "m"]
命名实体识别结果：[("Ns", "澳门")]
""")
        extractor = NERExtractor(self.temp_path)
        results = extractor.parse_results()
        assert len(results) > 0

    def test_convenience_function(self):
        """测试便捷函数"""
        self._write_ltp_results("""分词结果：['测试']
词性标注结果：['n']
命名实体识别结果：[]
""")
        result = extract_entities(self.temp_path)
        assert isinstance(result, list)

    def test_unknown_entity_type(self):
        """测试未知实体类型"""
        self._write_ltp_results("""分词结果：['某物']
词性标注结果：['n']
命名实体识别结果：[('Nx', '某物')]
""")
        extractor = NERExtractor(self.temp_path)
        entities = extractor.extract_entities()
        # 未知类型应保留原始编码
        assert entities[0]["type"] == "Nx"
