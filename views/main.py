"""首页：学习路线、进度概览、继续练习入口。"""

from flask import Blueprint, render_template
from flask_login import current_user
from sqlalchemy import select

from extensions import db
from models import Problem, Submission
from stats import compute_stats

bp = Blueprint("main", __name__)


@bp.route("/")
def index():
    problems = db.session.scalars(select(Problem).order_by(Problem.id)).all()
    tag_counts = {}
    for problem in problems:
        for tag in problem.tag_list:
            tag_counts[tag] = tag_counts.get(tag, 0) + 1

    stats = None
    recent = []
    next_problem = None
    if current_user.is_authenticated:
        stats = compute_stats(current_user.id)
        recent = db.session.scalars(
            select(Submission)
            .where(Submission.user_id == current_user.id)
            .order_by(Submission.created_at.desc(), Submission.id.desc())
            .limit(5)
        ).all()
        for problem in problems:
            if problem.id not in stats["solved_ids"]:
                next_problem = problem
                break

    return render_template(
        "index.html",
        problems=problems,
        tag_counts=tag_counts,
        stats=stats,
        recent=recent,
        next_problem=next_problem,
        easy_count=sum(1 for p in problems if p.difficulty == "入门"),
        normal_count=sum(1 for p in problems if p.difficulty == "基础"),
    )
