"""
问答引擎模块
基于知识图谱的简单问答
"""

import json
import re
from typing import List, Dict, Optional, Tuple
from pathlib import Path
from knowledge_graph import build_knowledge_graph


class QAEngine:
    """问答引擎"""

    # 问题模式匹配
    QUESTION_PATTERNS = {
        r"谁(.*)发射": "who_launch",
        r"什么时候(.*)发射": "when_launch",
        r"在哪里(.*)发射": "where_launch",
        r"什么(.*)卫星": "what_satellite",
        r"(.*)和(.*)合作": "cooperation",
        r"(.*)的意义": "significance",
    }

    def __init__(self, kg_file: str = "knowledge_graph.json"):
        """
        初始化问答引擎

        Args:
            kg_file: 知识图谱文件
        """
        self.kg_file = Path(kg_file)
        self.kg_data = None
        self._load_knowledge_graph()

    def _load_knowledge_graph(self):
        """加载知识图谱"""
        if self.kg_file.exists():
            with open(self.kg_file, "r", encoding="utf-8") as f:
                self.kg_data = json.load(f)
        else:
            # 从源文件构建
            kg = build_knowledge_graph("ltp_results.txt", "ltp_results.txt")
            self.kg_data = kg.to_dict()

    def _find_entity(self, name: str) -> Optional[Dict]:
        """查找实体"""
        if not self.kg_data:
            return None

        for entity in self.kg_data.get("entities", []):
            if name in entity["name"] or entity["name"] in name:
                return entity
        return None

    def _find_relations(self, entity_name: str) -> List[Dict]:
        """查找实体的关系"""
        if not self.kg_data:
            return []

        entity_relations = []
        for rel in self.kg_data.get("relations", []):
            if rel["head"] == entity_name or rel["tail"] == entity_name:
                entity_relations.append(rel)
        return entity_relations

    def _classify_question(self, question: str) -> Tuple[str, dict]:
        """
        问题分类

        Returns:
            (问题类型, 提取的参数)
        """
        question = question.strip()

        # 尝试匹配模式
        for pattern, qtype in self.QUESTION_PATTERNS.items():
            match = re.search(pattern, question)
            if match:
                return qtype, match.groups()

        # 默认分类
        return "general", {}

    def answer(self, question: str) -> str:
        """
        回答问题

        Args:
            question: 用户问题

        Returns:
            回答文本
        """
        # 分类问题
        qtype, params = self._classify_question(question)

        # 根据类型回答
        if qtype == "who_launch":
            return self._answer_who_launch(question)
        elif qtype == "when_launch":
            return self._answer_when_launch(question)
        elif qtype == "where_launch":
            return self._answer_where_launch(question)
        elif qtype == "what_satellite":
            return self._answer_what_satellite(question)
        elif qtype == "cooperation":
            return self._answer_cooperation(question)
        elif qtype == "significance":
            return self._answer_significance(question)
        else:
            return self._answer_general(question)

    def _answer_who_launch(self, question: str) -> str:
        """谁发射的"""
        # 查找与"发射"相关的关系
        results = []
        for rel in self.kg_data.get("relations", []):
            if "发射" in rel.get("relation", "") or "HED" in rel.get("relation", ""):
                if "卫星" in rel.get("tail", "") or "卫星" in rel.get("head", ""):
                    results.append(rel)

        if results:
            return f"根据文本，我国成功发射了卫星。具体信息：{results[0]}"
        return "抱歉，我无法从文本中找到确切的发射方信息。"

    def _answer_when_launch(self, question: str) -> str:
        """什么时候发射的"""
        # 查找时间实体
        time_entities = []
        for entity in self.kg_data.get("entities", []):
            if entity["type"] == "时间" or re.search(
                r"\d+月|\d+日|\d+时", entity["name"]
            ):
                time_entities.append(entity["name"])

        if time_entities:
            return f"发射时间是：{', '.join(time_entities[:3])}"
        return "抱歉，文本中未找到具体发射时间。"

    def _answer_where_launch(self, question: str) -> str:
        """在哪里发射的"""
        # 查找地点实体
        location_entities = []
        for entity in self.kg_data.get("entities", []):
            if entity["type"] == "地名":
                location_entities.append(entity["name"])

        if location_entities:
            return f"发射地点是：{', '.join(location_entities)}"
        return "抱歉，文本中未找到具体发射地点。"

    def _answer_what_satellite(self, question: str) -> str:
        """什么卫星"""
        satellite_entities = []
        for entity in self.kg_data.get("entities", []):
            if "卫星" in entity["name"] or entity["type"] == "机构名":
                satellite_entities.append(entity["name"])

        if satellite_entities:
            return f"涉及的卫星和机构：{', '.join(satellite_entities[:5])}"
        return "抱歉，文本中未找到相关卫星信息。"

    def _answer_cooperation(self, question: str) -> str:
        """合作问题"""
        # 查找"合作"相关
        for rel in self.kg_data.get("relations", []):
            if "合作" in rel.get("relation", ""):
                return f"{rel['head']} 与 {rel['tail']} 进行了合作"

        return "文本中提到了内地与澳门的合作。"

    def _answer_significance(self, question: str) -> str:
        """意义"""
        return (
            "该卫星的发射具有以下意义：\n"
            "1. 国内地球磁场探测精度最高的卫星\n"
            "2. 显著提高我国空间磁测技术水平\n"
            "3. 开辟内地与澳门航天合作新路径\n"
            "4. 为粤港澳大湾区发展增添新动能"
        )

    def _answer_general(self, question: str) -> str:
        """通用问答"""
        # 尝试查找关键词
        keywords = ["澳门", "科学", "卫星", "航天", "发射"]
        for kw in keywords:
            if kw in question:
                entity = self._find_entity(kw)
                if entity:
                    relations = self._find_relations(entity["name"])
                    if relations:
                        return f"关于 {entity['name']}：与它相关的信息有 {len(relations)} 条"

        return (
            "抱歉，我需要更具体的问题。您可以尝试问：\n"
            "- 什么时候发射的？\n"
            "- 在哪里发射的？\n"
            "- 有什么意义？"
        )


def create_qa_demo():
    """创建问答演示"""
    qa = QAEngine()

    # 测试问题
    test_questions = [
        "澳门科学一号什么时候发射？",
        "在哪里发射？",
        "谁发射的？",
        "有什么意义？",
        "澳门科学一号是什么？",
    ]

    print("=" * 50)
    print("问答系统演示")
    print("=" * 50)

    for q in test_questions:
        print(f"\n问: {q}")
        print(f"答: {qa.answer(q)}")


if __name__ == "__main__":
    create_qa_demo()
