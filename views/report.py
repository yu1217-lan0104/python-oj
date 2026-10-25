"""学习报告：可视化图表（服务端 SVG）+ Markdown / HTML 导出。"""

import io
from datetime import datetime, timedelta

from flask import Blueprint, render_template, request, send_file
from flask_login import current_user, login_required
from sqlalchemy import func, select

from charts import bar_chart, donut_chart, line_chart
from extensions import db
from models import MistakeNote, Submission
from stats import compute_stats

bp = Blueprint("report", __name__, url_prefix="/report")

STATUS_ORDER = ["AC", "WA", "TLE", "RE", "CE"]
STATUS_LABEL = {
    "AC": "通过",
    "WA": "答案错误",
    "TLE": "运行超时",
    "RE": "运行出错",
    "CE": "语法错误",
}
STATUS_COLOR = {
    "AC": "#0f9d58",
    "WA": "#ef4444",
    "TLE": "#f59e0b",
    "RE": "#c2410c",
    "CE": "#8b5cf6",
}


def _status_slices(user_id: int):
    rows = db.session.execute(
        select(Submission.status, func.count(Submission.id))
        .where(Submission.user_id == user_id)
        .group_by(Submission.status)
    ).all()
    counts = {status: count for status, count in rows}
    slices = [
        (f"{status} {STATUS_LABEL[status]}", counts[status], STATUS_COLOR[status])
        for status in STATUS_ORDER
        if counts.get(status)
    ]
    return slices, counts


def _daily_points(user_id: int, days: int = 14):
    today = datetime.now().date()
    start = today - timedelta(days=days - 1)
    rows = db.session.execute(
        select(Submission.created_at, Submission.status).where(
            Submission.user_id == user_id,
            Submission.created_at >= datetime.combine(start, datetime.min.time()),
        )
    ).all()
    totals = {start + timedelta(days=i): 0 for i in range(days)}
    for created, _status in rows:
        day = created.date()
        if day in totals:
            totals[day] += 1
    return [(day.strftime("%m-%d"), totals[day]) for day in sorted(totals)]


def _suggestions(stats: dict, counts: dict, mistakes: list) -> list:
    tips = []
    solved, total = stats["solved"], stats["total_problems"]
    if total and solved == 0:
        tips.append("还没有通过任何题目：建议从「入门」第 1 题开始，先熟悉「写代码 → 提交 → 看判题 → 进错题本」的完整流程。")
    elif total and solved == total:
        tips.append("全部题目都通过了：可以回头复习错题本，或者用更优的复杂度把通过过的题重写一遍。")
    else:
        tips.append(
            f"当前完成 {solved}/{total} 题（{stats['completion']}%）：建议跟着「专题训练」一组一组推进，比东做一题西做一题更容易形成手感。"
        )

    if stats["total_submits"] >= 5 and stats["pass_rate"] < 50:
        tips.append(
            f"通过率 {stats['pass_rate']}% 偏低：提交前先拿样例在本地跑一遍，重点核对输出里的空格、换行和大小写。"
        )

    untouched = [item for item in stats["by_tag"] if item["solved"] == 0]
    if untouched:
        names = "、".join(item["tag"] for item in untouched[:2])
        tips.append(f"「{names}」专题还没有通过记录，可以去「专题训练」挑一组集中突破。")

    if stats["unsolved_attempted"]:
        tips.append(
            f"有 {stats['unsolved_attempted']} 道题尝试过但还没通过：先看题目里的思路提示，再对照错题笔记复盘，别急着换题。"
        )

    if mistakes:
        tips.append(
            f"错题本里有 {len(mistakes)} 道题：把「错在哪、正确思路是什么」写清楚，比再刷 10 道新题更有用。"
        )
    else:
        tips.append("错题本还是空的：出现 WA/TLE 时顺手点一下「加入错题本」，复盘是提升最快的一步。")

    if counts.get("TLE"):
        tips.append(
            f"有 {counts['TLE']} 次运行超时：遇到 TLE 先看题目的数据范围，判断是死循环还是算法复杂度不够。"
        )
    return tips


def build_report(user_id: int) -> dict:
    stats = compute_stats(user_id)
    slices, counts = _status_slices(user_id)
    daily = _daily_points(user_id)
    tag_rows = [(item["tag"], item["solved"], item["total"]) for item in stats["by_tag"]]

    mistakes = db.session.scalars(
        select(MistakeNote)
        .where(MistakeNote.user_id == user_id)
        .order_by(MistakeNote.updated_at.desc(), MistakeNote.id.desc())
    ).all()
    recent = db.session.scalars(
        select(Submission)
        .where(Submission.user_id == user_id)
        .order_by(Submission.created_at.desc(), Submission.id.desc())
        .limit(10)
    ).all()

    return {
        "stats": stats,
        "slices": slices,
        "counts": counts,
        "daily": daily,
        "tag_rows": tag_rows,
        "mistakes": mistakes,
        "recent": recent,
        "suggestions": _suggestions(stats, counts, mistakes),
        "charts": {
            "donut": donut_chart(slices, center_label="提交"),
            "line": line_chart(daily),
            "bar": bar_chart(tag_rows),
        },
        "generated_at": datetime.now(),
    }


def build_markdown(report: dict, user) -> str:
    stats = report["stats"]
    lines = [
        "# Python 算法学习报告",
        "",
        f"- 账号：{user.display_name}（{user.username}）",
        f"- 生成时间：{report['generated_at']:%Y-%m-%d %H:%M}",
        "",
        "## 一、总体概览",
        "",
        "| 指标 | 数值 |",
        "| --- | --- |",
        f"| 已完成题目 | {stats['solved']} / {stats['total_problems']}（{stats['completion']}%） |",
        f"| 提交次数 | {stats['total_submits']}（通过 {stats['ac_submits']} 次） |",
        f"| 通过率 | {stats['pass_rate']}% |",
        f"| 错题本 | {stats['mistakes']} 题 |",
        "",
        "### 各难度进度",
        "",
        "| 难度 | 完成 | 进度 |",
        "| --- | --- | --- |",
    ]
    for level, item in stats["by_difficulty"].items():
        lines.append(f"| {level} | {item['solved']} / {item['total']} | {item['percent']}% |")

    lines += ["", "### 专题完成情况", "", "| 专题 | 完成 | 进度 |", "| --- | --- | --- |"]
    for item in stats["by_tag"]:
        lines.append(f"| {item['tag']} | {item['solved']} / {item['total']} | {item['percent']}% |")

    lines += ["", "### 提交结果分布", ""]
    if report["counts"]:
        for status in STATUS_ORDER:
            count = report["counts"].get(status)
            if count:
                lines.append(f"- {status}（{STATUS_LABEL[status]}）：{count} 次")
    else:
        lines.append("- 还没有提交记录")

    lines += ["", "## 二、错题清单", ""]
    if report["mistakes"]:
        for note in report["mistakes"]:
            summary = (note.content or "").replace("\n", " ").strip()
            if len(summary) > 60:
                summary = summary[:60] + "…"
            lines.append(f"- **{note.problem.title}**（{note.problem.difficulty}）{('：' + summary) if summary else ''}")
    else:
        lines.append("- 暂无错题记录")

    lines += ["", "## 三、最近提交", "", "| 时间 | 题目 | 结果 | 测试点 |", "| --- | --- | --- | --- |"]
    if report["recent"]:
        for item in report["recent"]:
            lines.append(
                f"| {item.created_at:%m-%d %H:%M} | {item.problem.title} | "
                f"{item.status} | {item.passed}/{item.total} |"
            )
    else:
        lines.append("| - | 暂无提交 | - | - |")

    lines += ["", "## 四、学习建议", ""]
    for index, tip in enumerate(report["suggestions"], start=1):
        lines.append(f"{index}. {tip}")

    lines += [
        "",
        "---",
        "",
        "由「Python 算法练习场」自动生成，仅供个人学习复盘使用。",
        "",
    ]
    return "\n".join(lines)


@bp.route("/")
@login_required
def index():
    report = build_report(current_user.id)
    return render_template("report/index.html", report=report, STATUS_LABEL=STATUS_LABEL)


@bp.route("/export")
@login_required
def export():
    fmt = (request.args.get("format") or "md").lower()
    report = build_report(current_user.id)
    stamp = report["generated_at"].strftime("%Y%m%d")

    if fmt == "html":
        content = render_template("report/export.html", report=report, user=current_user)
        return send_file(
            io.BytesIO(content.encode("utf-8")),
            mimetype="text/html; charset=utf-8",
            as_attachment=True,
            download_name=f"学习报告_{stamp}.html",
        )

    content = build_markdown(report, current_user)
    return send_file(
        io.BytesIO(content.encode("utf-8")),
        mimetype="text/markdown; charset=utf-8",
        as_attachment=True,
        download_name=f"学习报告_{stamp}.md",
    )
