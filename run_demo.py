#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
完整 NLP 处理流程演示

展示从原始文本到问答系统的全流程：
1. 文本预处理（加载、分句）
2. NER 实体识别
3. 关系抽取
4. 知识图谱构建
5. 问答引擎

依赖: Python 标准库 (无外部依赖)
"""

import sys
import os
import json
from pathlib import Path

# 添加 src 到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from _encoding import setup_encoding
from preprocessor import TextPreprocessor
from ner import NERExtractor
from relation import RelationExtractor
from knowledge_graph import KnowledgeGraph, build_knowledge_graph
from qa_engine import QAEngine


def print_section(title: str):
    """打印分节标题"""
    print(f"\n{'=' * 60}")
    print(f"  {title}")
    print(f"{'=' * 60}")


def demo_preprocessing(file_path: str):
    """演示文本预处理"""
    print_section("1. 文本预处理")

    preprocessor = TextPreprocessor()
    print(f"[输入文件] {file_path}")

    if not os.path.exists(file_path):
        print(f"[跳过] 文件不存在: {file_path}")
        return []

    # 加载
    text = preprocessor.load_text(file_path)
    print(f"[加载成功] 字符数: {len(text)}")

    # 规范化
    normalized = preprocessor.normalize(text)
    print(f"[规范化] 去除空格/换行后: {len(normalized)} 字符")

    # 分句
    sentences = preprocessor.split_sentences(normalized)
    print(f"[分句结果] 共 {len(sentences)} 句")
    for i, sent in enumerate(sentences[:5], 1):
        print(f"  {i}. {sent[:50]}{'...' if len(sent) > 50 else ''}")
    if len(sentences) > 5:
        print(f"  ... (还有 {len(sentences) - 5} 句)")

    return sentences


def demo_ner(result_file: str):
    """演示 NER 实体识别"""
    print_section("2. NER 实体识别")

    if not os.path.exists(result_file):
        print(f"[跳过] 文件不存在: {result_file}")
        print("[提示] NER 需要 LTP 处理结果文件 ltp_results.txt")
        print("[提示] 该文件通常由 LTP 工具处理文本后生成")
        return []

    extractor = NERExtractor(result_file)

    # 解析结果
    results = extractor.parse_results()
    print(f"[解析] 共 {len(results)} 句的 NER 结果")

    # 提取实体
    entities = extractor.extract_entities()
    print(f"[提取] 共 {len(entities)} 个实体")

    # 按类型分组
    unique = extractor.get_unique_entities(entities)
    for entity_type, words in unique.items():
        print(f"\n  [{entity_type}] ({len(words)} 个)")
        for word in words[:10]:
            print(f"    - {word}")
        if len(words) > 10:
            print(f"    ... (还有 {len(words) - 10} 个)")

    return entities


def demo_relation_extraction(result_file: str):
    """演示关系抽取"""
    print_section("3. 关系抽取")

    if not os.path.exists(result_file):
        print(f"[跳过] 文件不存在: {result_file}")
        return []

    extractor = RelationExtractor(result_file)

    # 解析依存分析
    dep_results = extractor.parse_dependency()
    print(f"[解析] 共 {len(dep_results)} 句的依存分析结果")

    # 提取关系
    relations = extractor.extract_relations()
    print(f"[提取] 共 {len(relations)} 条关系")

    # 显示主要关系类型
    rel_types = {}
    for rel in relations:
        rtype = rel["relation"]
        rel_types[rtype] = rel_types.get(rtype, 0) + 1

    print("\n[关系类型统计]")
    for rtype, count in sorted(rel_types.items(), key=lambda x: -x[1])[:10]:
        print(f"  {rtype}: {count} 条")

    print("\n[关系示例]")
    for rel in relations[:10]:
        print(f"  {rel['head_word']} --[{rel['relation']}]--> {rel['child_word']}")

    return relations


def demo_knowledge_graph(result_file: str):
    """演示知识图谱构建"""
    print_section("4. 知识图谱构建")

    if not os.path.exists(result_file):
        print(f"[跳过] 文件不存在: {result_file}")
        return None

    kg = build_knowledge_graph(result_file, result_file)

    print(f"[实体数量] {len(kg.entities)}")
    print(f"[关系数量] {len(kg.relations)}")

    print("\n[实体列表]")
    for entity in list(kg.entities)[:15]:
        etype = kg.entity_types.get(entity, "未知")
        print(f"  - {entity} ({etype})")
    if len(kg.entities) > 15:
        print(f"  ... (还有 {len(kg.entities) - 15} 个)")

    print("\n[关系示例]")
    for h, r, t in kg.relations[:10]:
        print(f"  {h} --[{r}]--> {t}")

    # 导出为 JSON
    kg_file = "knowledge_graph.json"
    with open(kg_file, "w", encoding="utf-8") as f:
        json.dump(kg.to_dict(), f, ensure_ascii=False, indent=2)
    print(f"\n[导出] 知识图谱已保存到: {kg_file}")

    # 导出为 Graphviz
    dot_file = "knowledge_graph.dot"
    with open(dot_file, "w", encoding="utf-8") as f:
        f.write(kg.to_graphviz())
    print(f"[导出] Graphviz 格式已保存到: {dot_file}")

    return kg


def demo_qa_engine(kg_file: str):
    """演示问答引擎"""
    print_section("5. 问答引擎")

    if not os.path.exists(kg_file):
        print(f"[跳过] 知识图谱文件不存在: {kg_file}")
        print("[提示] 请先运行本脚本生成知识图谱")
        return

    qa = QAEngine(kg_file)
    print(f"[加载] 知识图谱: {kg_file}")
    print(f"[实体数] {len(qa.kg_data.get('entities', []))}")
    print(f"[关系数] {len(qa.kg_data.get('relations', []))}")

    print("\n[问答演示]")
    questions = [
        "谁发射了卫星？",
        "什么时候发射的？",
        "在哪里发射？",
        "有什么意义？",
        "澳门科学一号是什么？",
        "有什么合作？",
    ]

    for q in questions:
        print(f"\n  问: {q}")
        a = qa.answer(q)
        print(f"  答: {a[:100]}{'...' if len(a) > 100 else ''}")

    print("\n[实体查找演示]")
    test_entities = ["澳门", "卫星", "发射"]
    for name in test_entities:
        entity = qa._find_entity(name)
        if entity:
            print(f"  '{name}' -> 找到: {entity['name']} (类型: {entity['type']})")
        else:
            print(f"  '{name}' -> 未找到")


def demo_standalone_mode():
    """演示独立模式（无数据文件时）"""
    print_section("独立模式演示")

    # 创建模拟数据
    import tempfile

    temp_file = tempfile.NamedTemporaryFile(
        mode="w", encoding="utf-8", delete=False, suffix=".txt"
    )
    temp_file.write(
        """分词结果：['澳门', '科学', '一号', '卫星', '成功', '发射']
词性标注结果：['ns', 'n', 'm', 'n', 'v', 'v']
命名实体识别结果：[('Ns', '澳门')]
依存句法分析结果：{'head': [4, 4, 4, 6, 6, 0], 'label': ['SBV', 'ATT', 'ATT', 'VOB', 'ADV', 'HED']}

分词结果：['该', '卫星', '用于', '科学', '实验']
词性标注结果：['r', 'n', 'v', 'n', 'n']
命名实体识别结果：[('Ni', '卫星')]
依存句法分析结果：{'head': [3, 3, 3, 6, 0], 'label': ['ATT', 'SBV', 'VOB', 'ADV', 'HED']}
"""
    )
    temp_file.close()

    print(f"[创建] 模拟数据文件: {temp_file.name}")

    # 从模拟数据构建知识图谱
    kg = build_knowledge_graph(temp_file.name, temp_file.name)
    print(f"\n[构建] 知识图谱")
    print(f"  实体数: {len(kg.entities)}")
    print(f"  关系数: {len(kg.relations)}")

    # 导出
    kg_file = "knowledge_graph_demo.json"
    with open(kg_file, "w", encoding="utf-8") as f:
        json.dump(kg.to_dict(), f, ensure_ascii=False, indent=2)
    print(f"[导出] {kg_file}")

    # 问答演示
    print("\n[问答演示]")
    qa = QAEngine(kg_file)
    questions = ["什么卫星？", "在哪里发射？"]

    for q in questions:
        print(f"\n  问: {q}")
        print(f"  答: {qa.answer(q)}")

    # 清理
    try:
        os.unlink(temp_file.name)
        os.unlink(kg_file)
    except:
        pass

    return True


def main():
    """主函数"""
    # 设置 UTF-8 输出
    setup_encoding()

    print("=" * 60)
    print("  Chinese Space QA - 完整 NLP 处理流程演示")
    print("=" * 60)

    # 确定数据文件路径
    script_dir = os.path.dirname(os.path.abspath(__file__))
    text_file = os.path.join(script_dir, "自然语言处理实验2-实验数据.txt")
    ltp_file = os.path.join(script_dir, "ltp_results.txt")

    print(f"\n[工作目录] {script_dir}")

    # 检查是否有数据文件
    has_text = os.path.exists(text_file)
    has_ltp = os.path.exists(ltp_file)

    if has_text or has_ltp:
        # 1. 文本预处理
        sentences = demo_preprocessing(text_file)

        # 2. NER
        entities = demo_ner(ltp_file)

        # 3. 关系抽取
        relations = demo_relation_extraction(ltp_file)

        # 4. 知识图谱
        kg = demo_knowledge_graph(ltp_file)

        # 5. 问答引擎
        demo_qa_engine("knowledge_graph.json")
    else:
        print("\n[提示] 未找到数据文件，进入独立演示模式")
        print("[提示] 将使用模拟数据展示完整流程\n")
        demo_standalone_mode()

    print_section("演示完成")
    print(f"\n生成的文件:")
    print(f"  - knowledge_graph.json  (知识图谱)")
    print(f"  - knowledge_graph.dot   (Graphviz 可视化)")
    print(f"\n使用 Graphviz 可视化知识图谱:")
    print(f"  dot -Tpng knowledge_graph.dot -o kg.png")


if __name__ == "__main__":
    main()
