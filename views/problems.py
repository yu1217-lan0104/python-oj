"""题库列表、题目详情与代码提交判题。"""

import json

from flask import (
    Blueprint,
    current_app,
    flash,
    redirect,
    render_template,
    request,
    url_for,
)
from flask_login import current_user, login_required
from sqlalchemy import select

import judge
from extensions import db
from models import MistakeNote, Problem, ProblemNote, Submission

bp = Blueprint("problems", __name__, url_prefix="/problems")

FILTER_STATES = [
    ("", "全部"),
    ("solved", "已通过"),
    ("attempted", "尝试中"),
    ("todo", "未开始"),
]


def _clip(text: str, limit: int = 1500) -> str:
    text = text or ""
    return text if len(text) <= limit else text[:limit] + f"\n…（共 {len(text)} 字符，已截断）"


def _status_map(user_id: int) -> dict:
    """problem_id -> 'AC' / 'TRIED'"""
    rows = db.session.execute(
        select(Submission.problem_id, Submission.status).where(Submission.user_id == user_id)
    ).all()
    result = {}
    for pid, status in rows:
        if status == "AC":
            result[pid] = "AC"
        elif result.get(pid) != "AC":
            result[pid] = "TRIED"
    return result


@bp.route("/")
def index():
    problems = db.session.scalars(select(Problem).order_by(Problem.id)).all()
    difficulty = (request.args.get("difficulty") or "").strip()
    tag = (request.args.get("tag") or "").strip()
    keyword = (request.args.get("keyword") or "").strip()
    state = (request.args.get("state") or "").strip()

    status_map = _status_map(current_user.id) if current_user.is_authenticated else {}

    all_tags = []
    for problem in problems:
        for item in problem.tag_list:
            if item not in all_tags:
                all_tags.append(item)

    filtered = []
    for problem in problems:
        if difficulty and problem.difficulty != difficulty:
            continue
        if tag and tag not in problem.tag_list:
            continue
        if keyword and keyword.lower() not in (problem.title + problem.description).lower():
            continue
        mark = status_map.get(problem.id, "")
        if state == "solved" and mark != "AC":
            continue
        if state == "attempted" and mark != "TRIED":
            continue
        if state == "todo" and mark:
            continue
        filtered.append(problem)

    return render_template(
        "problems/list.html",
        problems=filtered,
        total=len(problems),
        all_tags=all_tags,
        status_map=status_map,
        difficulty=difficulty,
        tag=tag,
        keyword=keyword,
        state=state,
        states=FILTER_STATES,
        easy_count=sum(1 for p in problems if p.difficulty == "入门"),
        normal_count=sum(1 for p in problems if p.difficulty == "基础"),
    )


@bp.route("/<int:pid>")
def detail(pid: int):
    problem = db.get_or_404(Problem, pid)
    status_map = _status_map(current_user.id) if current_user.is_authenticated else {}
    my_status = status_map.get(problem.id, "")

    recent = []
    mistake = None
    study_note = None
    if current_user.is_authenticated:
        recent = db.session.scalars(
            select(Submission)
            .where(Submission.user_id == current_user.id, Submission.problem_id == problem.id)
            .order_by(Submission.created_at.desc(), Submission.id.desc())
            .limit(5)
        ).all()
        mistake = db.session.scalar(
            select(MistakeNote).where(
                MistakeNote.user_id == current_user.id, MistakeNote.problem_id == problem.id
            )
        )
        study_note = db.session.scalar(
            select(ProblemNote).where(
                ProblemNote.user_id == current_user.id, ProblemNote.problem_id == problem.id
            )
        )

    prev_problem = db.session.scalar(
        select(Problem).where(Problem.id < problem.id).order_by(Problem.id.desc()).limit(1)
    )
    next_problem = db.session.scalar(
        select(Problem).where(Problem.id > problem.id).order_by(Problem.id.asc()).limit(1)
    )

    return render_template(
        "problems/detail.html",
        problem=problem,
        my_status=my_status,
        recent=recent,
        mistake=mistake,
        study_note=study_note,
        prev_problem=prev_problem,
        next_problem=next_problem,
        default_code="# 在这里写你的 Python3 代码\n# 用 input() 读入，print() 输出\n\n",
    )


@bp.post("/<int:pid>/submit")
@login_required
def submit(pid: int):
    problem = db.get_or_404(Problem, pid)
    code = (request.form.get("code") or "").replace("\r\n", "\n").rstrip()

    if not code.strip():
        flash("代码是空的，先写点内容再提交吧。", "warning")
        return redirect(url_for("problems.detail", pid=pid))

    max_bytes = current_app.config.get("JUDGE_MAX_CODE_BYTES", 64 * 1024)
    if len(code.encode("utf-8")) > max_bytes:
        flash(f"代码太长（超过 {max_bytes // 1024} KB），请精简后再提交。", "warning")
        return redirect(url_for("problems.detail", pid=pid))

    time_limit = problem.time_limit_ms or current_app.config.get("JUDGE_TIME_LIMIT_MS", 2000)
    result = judge.judge(
        code,
        problem.tests,
        time_limit_ms=time_limit,
        max_output=current_app.config.get("JUDGE_MAX_OUTPUT_BYTES", 256 * 1024),
    )

    rows = [
        {
            "index": case.index,
            "status": case.status,
            "time_ms": case.time_ms,
            "input": _clip(case.input_data),
            "expected": _clip(case.expected),
            "actual": _clip(case.actual),
            "message": case.message,
        }
        for case in result.cases
    ]

    submission = Submission(
        user_id=current_user.id,
        problem_id=problem.id,
        code=code,
        status=result.status,
        passed=result.passed,
        total=result.total,
        time_ms=result.time_ms,
        message=result.message,
        detail_json=json.dumps(rows, ensure_ascii=False),
    )
    db.session.add(submission)
    db.session.commit()

    if result.status == "AC":
        flash(f"「{problem.title}」恭喜通过！{result.total} 个测试点全部通过。", "success")
    elif result.status == "TLE":
        flash("运行超时：检查是否存在死循环，或换一个更快的算法。", "warning")
    else:
        flash(f"提交结果：{submission.status_text}，看看详情里的提示再试一次。", "danger")

    return redirect(url_for("records.detail", sid=submission.id))
