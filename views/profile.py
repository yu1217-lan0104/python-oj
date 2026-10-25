"""个人中心：刷题进度、专题完成情况、最近提交。"""

from flask import Blueprint, render_template
from flask_login import current_user, login_required
from sqlalchemy import select

from extensions import db
from models import Problem, Submission
from stats import compute_stats

bp = Blueprint("profile", __name__)


@bp.route("/profile")
@login_required
def index():
    stats = compute_stats(current_user.id)
    recent = db.session.scalars(
        select(Submission)
        .where(Submission.user_id == current_user.id)
        .order_by(Submission.created_at.desc(), Submission.id.desc())
        .limit(10)
    ).all()

    problems = db.session.scalars(select(Problem).order_by(Problem.id)).all()
    solved_problems = [p for p in problems if p.id in stats["solved_ids"]]
    unsolved_problems = [p for p in problems if p.id not in stats["solved_ids"]]

    return render_template(
        "profile.html",
        stats=stats,
        recent=recent,
        solved_problems=solved_problems[:8],
        next_problems=unsolved_problems[:5],
        user=current_user,
    )
