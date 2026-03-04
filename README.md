# chinese-space-qa - 航天知识问答系统

基于 LTP（语言技术平台）的中文 NLP 实验，实现从文本到问答的完整流水线。

## 功能特性

| 模块 | 功能 | 状态 |
|------|------|------|
| `preprocessor` | 文本预处理（编码检测/NFKC规范化/分句） | ✅ |
| `ner` | NER 命名实体识别 | ✅ |
| `relation` | 关系抽取（依存分析） | ✅ |
| `knowledge_graph` | 知识图谱构建 | ✅ |
| `qa_engine` | 问答引擎 | ✅ |

## 技术架构

```
文本数据 → 预处理 → LTP分析 → 实体识别 → 关系抽取 → 知识图谱 → 问答引擎
```

## 快速开始

### 环境要求

- Python 3.8+
- 无需额外依赖（直接解析 LTP 结果文件）

### 运行问答系统

```bash
python run_qa.py
```

### 交互式问答

```python
from src.qa_engine import QAEngine

qa = QAEngine()
answer = qa.answer("澳门科学一号在哪里发射？")
print(answer)
```

## 项目结构

```
NLP实验2/
├── src/
│   ├── __init__.py
│   ├── preprocessor.py       # 文本预处理
│   ├── ner.py              # NER 实体识别
│   ├── relation.py          # 关系抽取
│   ├── knowledge_graph.py  # 知识图谱
│   └── qa_engine.py        # 问答引擎
├── tests/                   # 测试文件
├── .claude/
│   ├── features.json       # 功能清单
│   ├── work-logs.json     # 工作日志
│   ├── workflow.py         # 工作流脚本
│   └── init.sh           # 初始化脚本
├── knowledge_graph.json    # 知识图谱数据
├── ltp_results.txt        # LTP 分析结果
├── run_qa.py             # 启动脚本
└── README.md
```

## 工作流

基于 [Anthropic《Effective harnesses for long-running agents》](https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents)：

1. **初始化** - 运行 `init.sh` 检查环境
2. **开发** - 每个会话完成一个 feature
3. **提交** - 自动 git commit
4. **重设计** - 每 5 轮重新评估任务

## 问答示例

```
问: 澳门科学一号在哪里发射？
答: 发射地点是：澳门

问: 有什么意义？
答: 该卫星的发射具有以下意义：
    1. 国内地球磁场探测精度最高的卫星
    2. 显著提高我国空间磁测技术水平
    3. 开辟内地与澳门航天合作新路径
    4. 为粤港澳大湾区发展增添新动能
```

## License

MIT
