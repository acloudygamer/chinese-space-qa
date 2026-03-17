"""
关系抽取模块
从依存句法分析中提取关系
"""

import json
import re
from typing import List, Dict, Tuple
from pathlib import Path
from parser import SafeParser


class RelationExtractor:
    """关系抽取器"""

    # 依存关系标签映射
    DEP_LABELS = {
        "SBV": "主谓关系",
        "VOB": "动宾关系",
        "POB": "介宾关系",
        "ATT": "定中关系",
        "ADV": "状中关系",
        "CMP": "补语关系",
        "COO": "并列关系",
        "SUB": "主补关系",
        "DBL": "兼语关系",
        "RAD": "右附加关系",
        "LAD": "左附加关系",
        "IS": "独立结构",
        "HED": "核心关系",
    }

    def __init__(self, result_file: str = "ltp_results.txt"):
        """
        初始化

        Args:
            result_file: LTP 结果文件路径
        """
        self.result_file = Path(result_file)

    def parse_dependency(self) -> List[Dict]:
        """
        解析依存分析结果

        Returns:
            依存分析结果列表
        """
        if not self.result_file.exists():
            raise FileNotFoundError(f"结果文件不存在: {self.result_file}")

        results = []
        current_sent = {}

        # 自动检测编码
        lines = []
        for encoding in ["utf-8", "gb18030", "gbk"]:
            try:
                with open(self.result_file, "r", encoding=encoding) as f:
                    lines = f.readlines()
                break
            except UnicodeDecodeError:
                continue

        if not lines:
            raise ValueError(f"无法解码文件: {self.result_file}")

        i = 0
        while i < len(lines):
            line = lines[i].strip()

            # 跳过空行
            if not line:
                i += 1
                continue

            if line.startswith("分词结果："):
                content = line.replace("分词结果：", "")
                words = self._parse_list_content(content)
                current_sent["words"] = words[0] if words and words[0] else []

            elif line.startswith("依存句法分析结果："):
                content = line.replace("依存句法分析结果：", "")
                dep = self._parse_dep_content(content)
                current_sent["dep"] = dep

                if current_sent.get("words"):
                    results.append(current_sent)
                current_sent = {}

            i += 1

        return results

    def _parse_list_content(self, content: str) -> List:
        """解析列表内容"""
        # 使用安全解析器
        parser = SafeParser()
        result = parser.parse_list_of_lists(content)
        if result:
            return result
        return []

    def _parse_dep_content(self, content: str) -> Dict:
        """解析依存分析内容"""
        # 格式: {'head': [5, 5, 4, 2, 0], 'label': ['SBV', 'ADV', 'ATT', 'POB', 'HED']}
        dep = {"head": [], "label": []}

        # 使用安全解析器
        parser = SafeParser()
        data = parser.parse_dict(content)

        if data:
            dep["head"] = data.get("head", [])
            dep["label"] = data.get("label", [])

        return dep

    def extract_relations(self, include_core: bool = False) -> List[Dict]:
        """
        提取关系

        Args:
            include_core: 是否包含核心关系 (HED)

        Returns:
            关系列表
        """
        results = self.parse_dependency()
        relations = []

        for sent_idx, sent in enumerate(results):
            words = sent.get("words", [])
            dep = sent.get("dep", {})
            heads = dep.get("head", [])
            labels = dep.get("label", [])

            # 遍历所有词，找出依存关系
            for idx, (head, label) in enumerate(zip(heads, labels)):
                if not include_core and label == "HED":
                    continue

                # 头节点索引（0 表示根节点，1-based in LTP）
                # head=0 表示依赖根节点，head>=1 表示依赖其他词
                if head >= 0 and head <= len(words):
                    if head == 0:
                        # 依赖根节点，关系方向为: 根节点 -> 当前词
                        head_word = "ROOT"
                    else:
                        head_word = words[head - 1]
                    child_word = words[idx]
                else:
                    continue

                relations.append(
                    {
                        "head_word": head_word,
                        "child_word": child_word,
                        "relation": self.DEP_LABELS.get(label, label),
                        "relation_code": label,
                        "sent_idx": sent_idx,
                    }
                )

        return relations

    def get_entity_relations(self, entities: List[Dict]) -> List[Dict]:
        """
        获取实体间的关系

        Args:
            entities: 实体列表

        Returns:
            实体间关系
        """
        # 提取所有关系
        all_relations = self.extract_relations()

        # 筛选出涉及实体的关系
        entity_words = set(e["word"] for e in entities)

        entity_relations = []
        for rel in all_relations:
            if rel["head_word"] in entity_words or rel["child_word"] in entity_words:
                entity_relations.append(rel)

        return entity_relations


# 便捷函数
def extract_relations(result_file: str = "ltp_results.txt") -> List[Dict]:
    """
    提取关系

    Args:
        result_file: LTP 结果文件

    Returns:
        关系列表
    """
    extractor = RelationExtractor(result_file)
    return extractor.extract_relations()


if __name__ == "__main__":
    # 测试
    from ner import NERExtractor

    # 提取实体
    ner = NERExtractor("ltp_results.txt")
    entities = ner.extract_entities()

    # 提取关系
    rel = RelationExtractor("ltp_results.txt")
    relations = rel.extract_relations()

    print("主要关系:")
    for r in relations[:15]:
        print(f"  {r['head_word']} --[{r['relation']}]--> {r['child_word']}")

    print("\n实体间关系:")
    entity_rels = rel.get_entity_relations(entities)
    for r in entity_rels:
        print(f"  {r['head_word']} --[{r['relation']}]--> {r['child_word']}")
