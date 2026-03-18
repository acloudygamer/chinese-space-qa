"""
知识图谱模块
构建实体-关系图谱
"""

import json
from typing import List, Dict, Set, Tuple
from pathlib import Path
from collections import defaultdict
from ner import NERExtractor
from relation import RelationExtractor


class KnowledgeGraph:
    """知识图谱"""

    # 无意义词/停用词列表
    STOPWORDS = {
        "的",
        "在",
        "和",
        "了",
        "与",
        "、",
        "是",
        "有",
        "我",
        "你",
        "他",
        "她",
        "它",
        "们",
        "这",
        "那",
        "个",
        "一",
        "不",
        "就",
        "也",
        "都",
        "而",
        "及",
        "与",
        "着",
        "或",
        "一个",
        "我们",
        "你们",
        "他们",
    }

    # 最小实体长度（过短的实体通常是噪音）
    MIN_ENTITY_LENGTH = 2

    def __init__(self):
        """初始化"""
        self.entities: Set[str] = set()
        self.entity_types: Dict[str, str] = {}  # entity -> type
        self.relations: List[Tuple[str, str, str]] = []  # (head, relation, tail)
        self.entity_relations: Dict[str, List[Tuple[str, str]]] = defaultdict(list)

    def _is_valid_entity(self, entity: str) -> bool:
        """
        检查实体是否有效

        Args:
            entity: 实体名称

        Returns:
            是否有效
        """
        if not entity:
            return False
        # 检查是否是停用词
        if entity in self.STOPWORDS:
            return False
        # 检查长度
        if len(entity) < self.MIN_ENTITY_LENGTH:
            return False
        # 检查是否全是标点
        if all(c in "，。、；：？！" for c in entity):
            return False
        return True

    def add_entity(self, entity: str, entity_type: str):
        """添加实体"""
        # 检查有效性
        if not self._is_valid_entity(entity):
            return
        self.entities.add(entity)
        # 如果类型是"未知"且不是停用词，保留
        if entity_type == "未知" or entity not in self.entity_types:
            self.entity_types[entity] = entity_type

    def add_relation(self, head: str, relation: str, tail: str):
        """添加关系"""
        # 验证实体有效性
        if not self._is_valid_entity(head) or not self._is_valid_entity(tail):
            return
        self.relations.append((head, relation, tail))
        self.entity_relations[head].append((relation, tail))
        # 反向关系
        self.entity_relations[tail].append((f"反向_{relation}", head))

    def build_from_extractors(self, ner_extractor, rel_extractor) -> "KnowledgeGraph":
        """
        从 NER 和 Relation 提取器构建图谱

        Args:
            ner_extractor: NERExtractor 实例
            rel_extractor: RelationExtractor 实例

        Returns:
            self
        """
        # 添加实体（来自 NER）
        entities = ner_extractor.extract_entities()
        for entity in entities:
            self.add_entity(entity["word"], entity["type"])

        # 添加关系（仅保留涉及有效实体的）
        all_relations = rel_extractor.extract_relations()
        entity_words = self.entities

        for rel in all_relations:
            head = rel["head_word"]
            tail = rel["child_word"]
            relation = rel["relation"]

            # 检查头尾是否有效
            head_valid = self._is_valid_entity(head)
            tail_valid = self._is_valid_entity(tail)

            # 如果头或尾是已有实体，添加关系
            if head in entity_words or tail in entity_words:
                # 如果需要添加新实体，只添加有效的
                if head not in entity_words and head_valid:
                    self.add_entity(head, "未知")
                if tail not in entity_words and tail_valid:
                    self.add_entity(tail, "未知")

                # 添加关系（如果头尾都有效）
                if head in self.entities and tail in self.entities:
                    self.add_relation(head, relation, tail)

        return self

    def get_entity_info(self, entity: str) -> Dict:
        """获取实体信息"""
        return {
            "name": entity,
            "type": self.entity_types.get(entity, "未知"),
            "relations": self.entity_relations.get(entity, []),
        }

    def query(self, entity: str, relation_type: str = None) -> List[str]:
        """
        查询

        Args:
            entity: 实体名
            relation_type: 关系类型（可选）

        Returns:
            查询结果
        """
        results = []
        for rel, tail in self.entity_relations.get(entity, []):
            if relation_type is None or rel == relation_type:
                results.append(tail)
        return results

    def to_dict(self) -> Dict:
        """导出为字典"""
        return {
            "entities": [
                {"name": e, "type": self.entity_types.get(e, "未知")}
                for e in self.entities
            ],
            "relations": [
                {"head": h, "relation": r, "tail": t} for h, r, t in self.relations
            ],
        }

    def to_neo4j_format(self) -> List[Dict]:
        """导出为 Neo4j 格式"""
        nodes = []
        for entity in self.entities:
            nodes.append({"id": entity, "label": self.entity_types.get(entity, "未知")})

        edges = []
        for head, relation, tail in self.relations:
            edges.append({"source": head, "target": tail, "type": relation})

        return {"nodes": nodes, "edges": edges}

    def to_graphviz(self) -> str:
        """导出为 Graphviz DOT 格式"""
        lines = ["digraph KnowledgeGraph {"]
        lines.append("  rankdir=LR;")

        # 节点
        for entity in self.entities:
            entity_type = self.entity_types.get(entity, "未知")
            lines.append(f'  "{entity}" [label="{entity}", type="{entity_type}"];')

        # 边
        for head, relation, tail in self.relations:
            lines.append(f'  "{head}" -> "{tail}" [label="{relation}"];')

        lines.append("}")
        return "\n".join(lines)


def build_knowledge_graph(
    ner_result_file: str = "ltp_results.txt", rel_result_file: str = "ltp_results.txt"
) -> KnowledgeGraph:
    """
    构建知识图谱

    Args:
        ner_result_file: NER 结果文件
        rel_result_file: 关系结果文件

    Returns:
        KnowledgeGraph 实例
    """
    ner = NERExtractor(ner_result_file)
    rel = RelationExtractor(rel_result_file)

    kg = KnowledgeGraph()
    kg.build_from_extractors(ner, rel)

    return kg


if __name__ == "__main__":
    # 构建图谱
    kg = build_knowledge_graph("ltp_results.txt", "ltp_results.txt")

    print("=" * 50)
    print("知识图谱")
    print("=" * 50)

    print(f"\n实体数量: {len(kg.entities)}")
    print(f"关系数量: {len(kg.relations)}")

    print("\n实体列表:")
    for entity in kg.entities:
        etype = kg.entity_types.get(entity, "未知")
        print(f"  - {entity} ({etype})")

    print("\n关系示例:")
    for h, r, t in kg.relations[:10]:
        print(f"  {h} --[{r}]--> {t}")

    # 保存为 JSON
    output_file = "knowledge_graph.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(kg.to_dict(), f, ensure_ascii=False, indent=2)
    print(f"\n已保存到: {output_file}")
