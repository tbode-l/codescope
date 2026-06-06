import subprocess
import sys
import os

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.stderr.reconfigure(encoding="utf-8", errors="replace")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

STEPS = [
    {
        "name": "tracker",
        "script": "tracker.py",
        "description": "GitHub API 搜索 + 下载 README",
    },
    {
        "name": "analyzer",
        "script": "analyzer.py",
        "description": "从 README 提取特征：技术栈、产品形态、安装复杂度",
    },
    {
        "name": "scorer",
        "script": "scorer.py",
        "description": "五维评分：活跃度、技术先进性、文档完整度、接入门槛、生态开放性",
    },
    {
        "name": "visualizer",
        "script": "visualizer.py",
        "description": "输出雷达图 + 散点图 + 柱状图 + 终端排名报告",
    },
]


def run_step(step):
    script_path = os.path.join(BASE_DIR, step["script"])
    if not os.path.exists(script_path):
        print(f"\n{'=' * 60}")
        print(f"  Step {step['name']}: {step['description']}")
        print(f"{'=' * 60}")
        print(f"\n  [跳过] {step['script']} 尚未实现（洪锋烨负责）\n")
        return 0

    print(f"\n{'=' * 60}")
    print(f"  Step {step['name']}: {step['description']}")
    print(f"{'=' * 60}\n")

    result = subprocess.run(
        [sys.executable, script_path],
        cwd=BASE_DIR,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )

    if result.stderr:
        print(result.stderr, file=sys.stderr)

    if result.returncode != 0:
        print(f"[失败] {step['script']} 退出码: {result.returncode}", file=sys.stderr)
        return result.returncode

    stdout = result.stdout.strip()
    if stdout:
        print(stdout)

    return 0


def main():
    print("=" * 60)
    print("  CodeScope — GitHub 代码增强工具自动化竞品分析系统")
    print("=" * 60)

    for step in STEPS:
        exit_code = run_step(step)
        if exit_code != 0:
            print(f"\n[中断] {step['name']} 失败，停止后续步骤", file=sys.stderr)
            sys.exit(exit_code)

    print(f"\n{'=' * 60}")
    print("  全部完成！")
    print(f"{'=' * 60}")
    print()
    print("  产出文件：")
    print("    known_competitors.json  — 已追踪仓库清单")
    print("    raw_data/                — 下载的 README 文件")
    print("    analysis.json            — 特征分析结果")
    print("    scores.json              — 评分排序结果")
    print("    output/*.png             — 4 张 Matplotlib 图表")
    print()


if __name__ == "__main__":
    main()