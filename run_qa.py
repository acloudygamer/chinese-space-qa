#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
问答系统启动脚本
"""

import sys
import io

# 解决 Windows 编码问题
if sys.platform == "win32":
    try:
        sys.stdout = io.TextIOWrapper(
            sys.stdout.buffer, encoding="utf-8", line_buffering=True, write_through=True
        )
    except Exception:
        pass

from src.qa_engine import QAEngine

qa = QAEngine()

test_questions = [
    "澳门科学一号什么时候发射？",
    "在哪里发射？",
    "有什么意义？",
]

print("=" * 50)
print("问答系统演示")
print("=" * 50)

for q in test_questions:
    print(f"\n问: {q}")
    print(f"答: {qa.answer(q)}")
