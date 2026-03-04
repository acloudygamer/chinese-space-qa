#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Long-Running Agent 工作流脚本
基于 Anthropic《Effective harnesses for long-running agents》

功能:
- 循环执行任务会话
- 任务重设计机制（每 N 轮）
- 自动清理无用文件
- Git 版本管理
"""

# Windows UTF-8 支持
import io

if sys.platform == "win32":
    try:
        sys.stdout = io.TextIOWrapper(
            sys.stdout.buffer, encoding="utf-8", line_buffering=True
        )
    except Exception:
        pass

import json
import os
import sys
import subprocess
from datetime import datetime
from pathlib import Path

# 配置
PROJECT_DIR = Path(__file__).parent.parent
CLAUDE_DIR = PROJECT_DIR / ".claude"
FEATURES_FILE = CLAUDE_DIR / "features.json"
LOGS_FILE = CLAUDE_DIR / "work-logs.json"
INIT_SCRIPT = CLAUDE_DIR / "init.sh"

# 工作流配置
CONFIG = {
    "max_sessions": 100,  # 最大会话数
    "redesign_interval": 5,  # 每 N 轮任务重设计
    "auto_cleanup": True,  # 自动清理无用文件
    "require_clean_state": True,  # 要求 clean 状态
    "auto_commit": True,  # 自动提交
    "coverage_threshold": 80,  # 覆盖率要求
}


def load_json(file_path):
    """加载 JSON 文件"""
    if not file_path.exists():
        return None
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(file_path, data):
    """保存 JSON 文件"""
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def run_command(cmd, cwd=None, capture=True):
    """运行命令"""
    try:
        if capture:
            result = subprocess.run(
                cmd,
                shell=True,
                cwd=cwd or PROJECT_DIR,
                capture_output=True,
                text=True,
                timeout=300,
            )
            return result.returncode, result.stdout, result.stderr
        else:
            return (
                subprocess.run(cmd, shell=True, cwd=cwd or PROJECT_DIR).returncode,
                "",
                "",
            )
    except subprocess.TimeoutExpired:
        return -1, "", "Command timeout"
    except Exception as e:
        return -1, "", str(e)


def init_environment():
    """初始化环境"""
    print("=" * 50)
    print("初始化环境...")
    print("=" * 50)

    # 加载 features
    features = load_json(FEATURES_FILE)
    if not features:
        print("ERROR: features.json 不存在")
        sys.exit(1)

    # 运行 init.sh
    if INIT_SCRIPT.exists():
        print("运行 init.sh...")
        code, stdout, stderr = run_command(f"bash {INIT_SCRIPT}", capture=False)
        if code != 0:
            print(f"WARNING: init.sh 运行失败: {stderr}")

    # 显示当前进度
    session = features.get("project", {}).get("session", 1)
    current = features.get("progress", {}).get("current_feature", "N/A")
    print(f"\n当前会话: {session}")
    print(f"当前功能: {current}")
    print()

    return features


def check_git_status():
    """检查 Git 状态"""
    code, stdout, _ = run_command("git status --short")
    if code == 0:
        return stdout.strip()
    return ""


def auto_cleanup():
    """自动清理无用文件"""
    print("检查无用文件...")

    # 需要检查的目录
    check_dirs = [PROJECT_DIR / "tests", PROJECT_DIR]

    # 无用文件模式
    patterns = ["*.pyc", "__pycache__", "*.log", ".pytest_cache", "*.tmp", "temp_*"]

    removed = []
    for check_dir in check_dirs:
        if not check_dir.exists():
            continue
        for pattern in patterns:
            code, stdout, _ = run_command(
                f'find "{check_dir}" -name "{pattern}" -type f 2>/dev/null'
            )
            if code == 0 and stdout.strip():
                for f in stdout.strip().split("\n"):
                    if f:
                        try:
                            os.remove(f)
                            removed.append(f)
                        except:
                            pass

    if removed:
        print(f"已清理 {len(removed)} 个无用文件")
    else:
        print("无无用文件")

    return removed


def check_coverage():
    """检查测试覆盖率"""
    code, stdout, stderr = run_command(
        "pytest --cov=. --cov-report=json -q 2>/dev/null"
    )

    if code == 0:
        # 解析覆盖率
        cov_file = PROJECT_DIR / "coverage.json"
        if cov_file.exists():
            data = load_json(cov_file)
            if data:
                total = data.get("totals", {}).get("percent_covered", 0)
                return total >= CONFIG["coverage_threshold"], total

    return None, 0


def update_progress(features, completed_feature=None, new_session=False):
    """更新进度"""
    session = features.get("project", {}).get("session", 1)

    if new_session:
        session += 1
        features["project"]["session"] = session
        features["progress"]["status"] = "in_progress"

    if completed_feature:
        # 从 in_progress 移到 completed
        in_progress = features["progress"]["in_progress"]
        completed = features["progress"]["completed"]

        for i, item in enumerate(in_progress):
            if item["feature"] == completed_feature:
                in_progress.pop(i)
                item["status"] = "passing"
                completed.append(item)
                break

        # 更新 features 列表
        for f in features["features"]:
            if f["name"] == completed_feature:
                f["status"] = "passing"

        # 激活下一个 pending
        pending = features["progress"]["pending"]
        if pending:
            next_item = pending.pop(0)
            next_item["status"] = "developing"
            next_item["started_at"] = datetime.now().isoformat()
            features["progress"]["in_progress"] = [next_item]
            features["progress"]["current_feature"] = next_item["feature"]

    save_json(FEATURES_FILE, features)
    return features


def add_work_log(session, agent, action_type, actions, artifacts, git_info=None):
    """添加工作日志"""
    logs = load_json(LOGS_FILE)
    if not logs:
        logs = {"logs": [], "session_contexts": {}}

    log_entry = {
        "session": session,
        "date": datetime.now().isoformat(),
        "agent": agent,
        "type": action_type,
        "actions": actions,
        "artifacts": artifacts,
        "git": git_info or {"branch": None, "commit": None, "pushed": False},
    }

    logs["logs"].append(log_entry)

    # 更新 session 上下文
    logs["session_contexts"][str(session)] = artifacts

    save_json(LOGS_FILE, logs)


def git_commit(features):
    """Git 提交"""
    session = features.get("project", {}).get("session", 1)
    current = features.get("progress", {}).get("current_feature", "unknown")

    # 检查是否有更改
    status = check_git_status()
    if not status:
        print("无更改，无需提交")
        return None

    # 添加文件
    run_command("git add .")

    # 生成提交信息
    commit_msg = f"feat: {session}-{current} 完成本轮任务"

    # 提交
    code, stdout, stderr = run_command(f'git commit -m "{commit_msg}"')

    if code == 0:
        print(f"已提交: {commit_msg}")
        return commit_msg
    else:
        print(f"提交失败: {stderr}")
        return None


def task_redesign(features):
    """任务重设计"""
    print("=" * 50)
    print("执行任务重设计...")
    print("=" * 50)

    session = features.get("project", {}).get("session", 1)

    # 分析当前状态
    completed = features.get("progress", {}).get("completed", [])
    pending = features.get("progress", {}).get("pending", [])

    print(f"已完成: {len(completed)} 个功能")
    print(f"待完成: {len(pending)} 个功能")

    # 这里可以添加 AI 分析逻辑
    # 例如：根据完成情况调整任务优先级、合并小任务、拆分大任务等

    # 重置会话计数
    features["project"]["session"] = 1

    # 保存
    save_json(FEATURES_FILE, features)

    # 添加重设计日志
    add_work_log(
        session=session,
        agent="workflow",
        action_type="redesign",
        actions=["任务重设计"],
        artifacts={
            "completed_count": len(completed),
            "pending_count": len(pending),
            "reason": f"每 {CONFIG['redesign_interval']} 轮重设计",
        },
    )

    print("任务重设计完成")
    return features


def run_session(features):
    """运行单个会话"""
    session = features.get("project", {}).get("session", 1)

    print("=" * 50)
    print(f"开始会话 {session}")
    print("=" * 50)

    # 这里会启动 Claude Code 会话
    # 用户需要在 Claude Code 中手动执行任务

    print("\n请在 Claude Code 中执行任务")
    print("完成后请回复 'done' 以继续")
    print()

    user_input = input("完成后输入 done: ").strip().lower()

    if user_input == "done":
        # 任务完成处理
        current = features.get("progress", {}).get("current_feature")

        if current:
            features = update_progress(features, completed_feature=current)

        # Git 提交
        if CONFIG["auto_commit"]:
            git_commit(features)

        # 自动清理
        if CONFIG["auto_cleanup"]:
            auto_cleanup()

        # 检查是否需要重设计
        if session % CONFIG["redesign_interval"] == 0:
            features = task_redesign(features)

        return features

    return features


def main():
    """主循环"""
    print("Long-Running Agent 工作流")
    print(f"项目: {PROJECT_DIR.name}")
    print(f"重设计间隔: 每 {CONFIG['redesign_interval']} 轮")
    print()

    # 初始化
    features = init_environment()

    # 主循环
    session_count = 0
    while session_count < CONFIG["max_sessions"]:
        # 运行会话
        features = run_session(features)

        session_count = features.get("project", {}).get("session", 1)

        # 询问是否继续
        print()
        cont = input("是否继续下一轮会话? (y/n): ").strip().lower()
        if cont != "y":
            break

    print("\n工作流结束")
    print(f"总会话数: {session_count}")


if __name__ == "__main__":
    main()
