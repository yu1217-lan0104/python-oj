"""专题训练：把题目编成有顺序的套题，跟踪每组完成度。"""

from flask import Blueprint, render_template
from flask_login import current_user
from sqlalchemy import select

from extensions import db
from models import Problem, Submission, Topic

bp = Blueprint("topics", __name__, url_prefix="/topics")


def _progress() -> dict:
    """problem_id -> 'AC' / 'TRIED'"""
    if not current_user.is_authenticated:
        return {}
    rows = db.session.execute(
        select(Submission.problem_id, Submission.status).where(
            Submission.user_id == current_user.id
        )
    ).all()
    result = {}
    for pid, status in rows:
        if status == "AC":
            result[pid] = "AC"
        elif result.get(pid) != "AC":
            result[pid] = "TRIED"
    return result


def _first_unsolved(problems, progress):
    for problem in problems:
        if progress.get(problem.id) != "AC":
            return problem
    return None


@bp.route("/")
def index():
    topics = db.session.scalars(select(Topic).order_by(Topic.sort_order, Topic.id)).all()
    progress = _progress()
    rows = []
    for topic in topics:
        problems = topic.problems
        solved = sum(1 for p in problems if progress.get(p.id) == "AC")
        total = len(problems)
        rows.append(
            {
                "topic": topic,
                "total": total,
                "solved": solved,
                "percent": round(solved / total * 100) if total else 0,
                "next_problem": _first_unsolved(problems, progress),
                "done": total > 0 and solved == total,
            }
        )
    total_solved = sum(row["solved"] for row in rows)
    total_problems = sum(row["total"] for row in rows)
    return render_template(
        "topics/list.html",
        rows=rows,
        total_solved=total_solved,
        total_problems=total_problems,
    )


@bp.route("/<int:tid>")
def detail(tid: int):
    topic = db.get_or_404(Topic, tid)
    progress = _progress()
    items = []
    for index, problem in enumerate(topic.problems, start=1):
        state = progress.get(problem.id, "")
        items.append({"index": index, "problem": problem, "state": state})
    solved = sum(1 for item in items if item["state"] == "AC")
    next_problem = _first_unsolved(topic.problems, progress)
    return render_template(
        "topics/detail.html",
        topic=topic,
        items=items,
        solved=solved,
        total=len(items),
        percent=round(solved / len(items) * 100) if items else 0,
        next_problem=next_problem,
    )
