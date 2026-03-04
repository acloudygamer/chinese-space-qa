#!/bin/bash
# NLP实验2 - 环境初始化脚本
# 基于 Effective harnesses for long-running agents 模式

set -e

echo "=========================================="
echo "NLP实验2 - 环境初始化"
echo "=========================================="

# 1. 检查 Python 环境
echo "[1/4] 检查 Python 环境..."
python --version

# 2. 检查并安装依赖
echo "[2/4] 检查依赖..."
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt
else
    echo "跳过: 未找到 requirements.txt"
fi

# 3. 检查 LTP 模型
echo "[3/4] 检查 LTP 模型..."
if [ -d "small1" ]; then
    echo "LTP 模型已存在: small1/"
else
    echo "警告: 未找到 LTP 模型目录 small1/"
fi

# 4. 运行基础测试
echo "[4/4] 运行基础测试..."
if [ -d "tests" ]; then
    pytest tests/ -v --tb=short || echo "测试完成（可能有失败）"
else
    echo "跳过: 未找到 tests/ 目录"
fi

echo "=========================================="
echo "初始化完成！"
echo "查看 progress: cat .claude/features.json"
echo "=========================================="
