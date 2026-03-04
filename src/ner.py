"""
NER 实体识别模块
基于 LTP 进行命名实体识别
"""

from typing import List, Dict, Tuple, Optional
from pathlib import Path


class NERExtractor:
    """命名实体识别器"""

    # LTP NER 标签映射
    NER_LABELS = {
        "Nh": "人名",
        "Ns": "地名",
        "Ni": "机构名",
        "Nt": "时间",
    }

    def __init__(self, model_dir: str = "small1"):
        """
        初始化 NER 提取器

        Args:
            model_dir: LTP 模型目录
        """
        self.model_dir = Path(model_dir)
        self._ltp = None

    def _load_ltp(self):
        """延迟加载 LTP 模型"""
        if self._ltp is None:
            try:
                from ltp import LTP

                self._ltp = LTP(str(self.model_dir))
            except ImportError:
                raise ImportError("请安装 ltp: pip install ltp")
            except Exception as e:
                raise RuntimeError(f"加载 LTP 模型失败: {e}")

    def extract(self, sentences: List[str]) -> List[Dict]:
        """
        从句子列表中提取实体

        Args:
            sentences: 句子列表

        Returns:
            实体列表，每项包含 {word, type, start, end}
        """
        self._load_ltp()

        results = []
        for sent_idx, sentence in enumerate(sentences):
            # 分词
            seg_result = self._ltp.pipeline([sentence], tasks=["cws", "ner"])
            words = seg_result[0][0]
            ner_tags = seg_result[1][0]

            # 提取实体
            entities = self._extract_entities_from_tags(words, ner_tags, sent_idx)
            results.extend(entities)

        return results

    def _extract_entities_from_tags(
        self, words: List[str], ner_tags: List[str], sent_idx: int
    ) -> List[Dict]:
        """从 NER 标签中提取实体"""
        entities = []
        current_entity = None
        current_type = None
        start_pos = 0

        for i, (word, tag) in enumerate(zip(words, ner_tags)):
            if tag.startswith("S-"):  # 单字实体
                entity_type = tag[2:]
                entities.append(
                    {
                        "word": word,
                        "type": self.NER_LABELS.get(entity_type, entity_type),
                        "type_code": entity_type,
                        "sent_idx": sent_idx,
                        "start": start_pos,
                        "end": start_pos + len(word),
                    }
                )
            elif tag.startswith("B-"):  # 实体开始
                if current_entity:
                    # 保存前一个实体
                    entities.append(current_entity)
                current_entity = word
                current_type = tag[2:]
                start_pos = sum(len(w) for w in words[:i])
            elif tag.startswith("E-"):  # 实体结束
                if current_entity:
                    current_entity += word
                    entities.append(
                        {
                            "word": current_entity,
                            "type": self.NER_LABELS.get(current_type, current_type),
                            "type_code": current_type,
                            "sent_idx": sent_idx,
                            "start": start_pos,
                            "end": start_pos + len(current_entity),
                        }
                    )
                    current_entity = None
                    current_type = None
            elif tag.startswith("I-"):  # 实体中间
                if current_entity:
                    current_entity += word

            start_pos += len(word)

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
def extract_entities(sentences: List[str], model_dir: str = "small1") -> List[Dict]:
    """
    提取实体

    Args:
        sentences: 句子列表
        model_dir: LTP 模型目录

    Returns:
        实体列表
    """
    extractor = NERExtractor(model_dir)
    return extractor.extract(sentences)


if __name__ == "__main__":
    # 测试
    from preprocessor import TextPreprocessor

    # 预处理
    preprocessor = TextPreprocessor()
    sentences = preprocessor.process("自然语言处理实验2-实验数据.txt")

    # NER
    extractor = NERExtractor("small1")
    entities = extractor.extract(sentences[:3])  # 测试前3句

    print("提取的实体:")
    for e in entities:
        print(f"  {e['word']} ({e['type']})")

    print("\n按类型分组:")
    unique = extractor.get_unique_entities(entities)
    for type_name, words in unique.items():
        print(f"  {type_name}: {words}")
