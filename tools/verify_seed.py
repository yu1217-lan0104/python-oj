"""开发期自检脚本：校验题库参考解、专题套题与语法卡片数据。

用法：.venv\\Scripts\\python.exe tools\\verify_seed.py
"""

import os
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

import judge  # noqa: E402
from cards_data import CARDS  # noqa: E402
from seed_data import PROBLEMS  # noqa: E402
from topics_data import TOPICS  # noqa: E402


def check_topics_and_cards() -> int:
    """专题引用的题目必须存在；卡片标题不能重复。"""
    failures = 0
    titles = {item["title"] for item in PROBLEMS}

    covered = []
    for topic in TOPICS:
        for title in topic["problems"]:
            if title not in titles:
                failures += 1
                print(f"  [MISS] 专题「{topic['name']}」引用了不存在的题目：{title}")
            else:
                covered.append(title)
    uncovered = titles - set(covered)
    duplicates = len(covered) - len(set(covered))

    print(
        f"[专题] {len(TOPICS)} 个专题，覆盖 {len(set(covered))}/{len(titles)} 道题"
        f"，重复引用 {duplicates} 次"
    )
    if uncovered:
        print(f"  [WARN] 以下题目还没有编入任何专题：{'、'.join(sorted(uncovered))}")

    card_titles = [card["title"] for card in CARDS]
    repeated = len(card_titles) - len(set(card_titles))
    categories = {}
    for card in CARDS:
        categories[card["category"]] = categories.get(card["category"], 0) + 1
    detail = "、".join(f"{name} {count}" for name, count in categories.items())
    print(f"[卡片] {len(CARDS)} 张，分类：{detail}")
    if repeated:
        failures += 1
        print(f"  [FAIL] 有 {repeated} 张卡片标题重复")
    return failures


def main() -> int:
    failures = 0
    total_cases = 0
    started = time.perf_counter()
    for problem in PROBLEMS:
        if "reference" not in problem:
            continue
        tests = problem["tests"]
        total_cases += len(tests)
        result = judge.judge(problem["reference"], tests, time_limit_ms=3000)
        if result.status != "AC":
            failures += 1
            print(f"[FAIL] {problem['title']}: {result.status} / {result.message}")
            for case in result.cases:
                if case.status != "AC":
                    print(f"        第 {case.index} 个测试点")
                    print(f"        期望: {case.expected!r}")
                    print(f"        实际: {case.actual!r}")
                    break
        else:
            print(f"[ OK ] {problem['title']}  ({len(tests)} 个测试点, {result.time_ms} ms)")

    print(f"\n共 {len(PROBLEMS)} 题 / {total_cases} 个测试点，耗时 {time.perf_counter() - started:.1f}s")
    if failures:
        print(f"有 {failures} 题的参考解未通过，请检查测试数据！")

    failures += check_topics_and_cards()
    print()
    if failures:
        print(f"自检未通过，共 {failures} 处问题。")
    else:
        print("题库、专题、卡片数据自检全部通过 ✅")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())

