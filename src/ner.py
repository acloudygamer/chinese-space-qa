"""
NER 实体识别模块
从 ltp_results.txt 解析实体
"""

import re
import json
from typing import List, Dict
from pathlib import Path


class NERExtractor:
    """命名实体识别器"""

    # NER 类型映射
    NER_LABELS = {
        "Nh": "人名",
        "Ns": "地名",
        "Ni": "机构名",
        "Nt": "时间",
    }

    def __init__(self, result_file: str = "ltp_results.txt"):
        """
        初始化

        Args:
            result_file: LTP 结果文件路径
        """
        self.result_file = Path(result_file)

    def parse_results(self) -> List[Dict]:
        """
        解析 ltp_results.txt

        Returns:
            解析结果列表
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

            if line.startswith("分词结果："):
                # 提取分词结果
                content = line.replace("分词结果：", "")
                words = self._parse_list_content(content)
                current_sent["words"] = words

            elif line.startswith("词性标注结果："):
                content = line.replace("词性标注结果：", "")
                pos_tags = self._parse_list_content(content)
                current_sent["pos"] = pos_tags

            elif line.startswith("命名实体识别结果："):
                content = line.replace("命名实体识别结果：", "")
                entities = self._parse_ner_content(content)
                current_sent["ner"] = entities

                # 一句完整，添加到结果
                if current_sent.get("words"):
                    results.append(current_sent)
                current_sent = {}

            i += 1

        return results

    def _parse_list_content(self, content: str) -> List:
        """解析列表内容"""
        try:
            # 尝试 JSON 解析
            return json.loads(content)
        except:
            # 备用：正则提取
            match = re.search(r"\[(.*)\]", content)
            if match:
                inner = match.group(1)
                if "'" in inner:
                    # 字符串列表
                    items = re.findall(r"'([^']+)'", inner)
                    return [items]
                elif inner.strip():
                    return [[inner.strip()]]
            return []

    def _parse_ner_content(self, content: str) -> List[tuple]:
        """解析 NER 内容"""
        entities = []

        # 匹配 (类型, 实体) 模式
        # 例如: [('Ni', '国家航天局'), ('Ns', '澳门')]
        pattern = r"\('([^']+)',\s*'([^']+)'\)"
        matches = re.findall(pattern, content)

        for ner_type, entity in matches:
            entities.append((ner_type, entity))

        return entities

    def extract_entities(self) -> List[Dict]:
        """
        提取所有实体

        Returns:
            实体列表
        """
        results = self.parse_results()
        entities = []

        for sent_idx, sent in enumerate(results):
            words = sent.get("words", [[]])[0] if sent.get("words") else []
            ner_tags = sent.get("ner", [])

            for ner_type, entity in ner_tags:
                entities.append(
                    {
                        "word": entity,
                        "type": self.NER_LABELS.get(ner_type, ner_type),
                        "type_code": ner_type,
                        "sent_idx": sent_idx,
                    }
                )

        return entities

    def get_unique_entities(self, entities: List[Dict]) -> Dict[str, List[str]]:
        """
        获取唯一实体（按类型分组）

        Args:
            entities: 实体列表

        Returns:
            {类型: [实体列表]}
        """
        unique = {}
        for entity in entities:
            entity_type = entity["type"]
            word = entity["word"]
            if entity_type not in unique:
                unique[entity_type] = []
            if word not in unique[entity_type]:
                unique[entity_type].append(word)
        return unique


# 便捷函数
def extract_entities(result_file: str = "ltp_results.txt") -> List[Dict]:
    """
    提取实体

    Args:
        result_file: LTP 结果文件

    Returns:
        实体列表
    """
    extractor = NERExtractor(result_file)
    return extractor.extract_entities()


if __name__ == "__main__":
    # 测试
    extractor = NERExtractor("ltp_results.txt")
    entities = extractor.extract_entities()

    print("提取的实体:")
    for e in entities:
        print(f"  {e['word']} ({e['type']})")

    print("\n按类型分组:")
    unique = extractor.get_unique_entities(entities)
    for t, words in unique.items():
        print(f"  {t}: {words}")
