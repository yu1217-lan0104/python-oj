"""提交记录、判题详情、错题本与解题笔记。"""

import json

from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from sqlalchemy import select

from extensions import db
from models import MistakeNote, Problem, ProblemNote, Submission
from utils import clamp_int

bp = Blueprint("records", __name__)

PAGE_SIZE = 12


@bp.route("/submissions")
@login_required
def submissions():
    page = clamp_int(request.args.get("page"), 1, 1, 100000)
    status = (request.args.get("status") or "").strip()
    problem_id = clamp_int(request.args.get("problem_id"), 0, 0, 10**9)

    stmt = select(Submission).where(Submission.user_id == current_user.id)
    if status:
        stmt = stmt.where(Submission.status == status)
    if problem_id:
        stmt = stmt.where(Submission.problem_id == problem_id)
    stmt = stmt.order_by(Submission.created_at.desc(), Submission.id.desc())

    pagination = db.paginate(stmt, page=page, per_page=PAGE_SIZE, error_out=False)
    problem_title = None
    if problem_id:
        problem = db.session.get(Problem, problem_id)
        problem_title = problem.title if problem else None

    return render_template(
        "records/submissions.html",
        pagination=pagination,
        items=pagination.items,
        status=status,
        problem_id=problem_id,
        problem_title=problem_title,
        statuses=["AC", "WA", "TLE", "RE", "CE"],
    )


@bp.route("/submissions/<int:sid>")
@login_required
def detail(sid: int):
    submission = db.session.get(Submission, sid)
    if not submission or submission.user_id != current_user.id:
        abort(404)

    try:
        cases = json.loads(submission.detail_json or "[]")
    except json.JSONDecodeError:
        cases = []

    note = db.session.scalar(
        select(MistakeNote).where(
            MistakeNote.user_id == current_user.id,
            MistakeNote.problem_id == submission.problem_id,
        )
    )
    history = db.session.scalars(
        select(Submission)
        .where(
            Submission.user_id == current_user.id,
            Submission.problem_id == submission.problem_id,
            Submission.id != submission.id,
        )
        .order_by(Submission.created_at.desc(), Submission.id.desc())
        .limit(5)
    ).all()

    return render_template(
        "records/detail.html",
        submission=submission,
        problem=submission.problem,
        cases=cases,
        note=note,
        history=history,
        code_lines=submission.code.split("\n"),
    )


@bp.route("/mistakes")
@login_required
def mistakes():
    notes = db.session.scalars(
        select(MistakeNote)
        .where(MistakeNote.user_id == current_user.id)
        .order_by(MistakeNote.updated_at.desc(), MistakeNote.id.desc())
    ).all()

    last_status = {}
    if notes:
        problem_ids = [note.problem_id for note in notes]
        rows = db.session.execute(
            select(Submission.problem_id, Submission.status, Submission.created_at)
            .where(
                Submission.user_id == current_user.id,
                Submission.problem_id.in_(problem_ids),
            )
            .order_by(Submission.created_at.asc(), Submission.id.asc())
        ).all()
        for pid, status, _created in rows:
            last_status[pid] = status

    return render_template("records/mistakes.html", notes=notes, last_status=last_status)


@bp.post("/mistakes/<int:pid>/toggle")
@login_required
def toggle_mistake(pid: int):
    problem = db.get_or_404(Problem, pid)
    note = db.session.scalar(
        select(MistakeNote).where(
            MistakeNote.user_id == current_user.id, MistakeNote.problem_id == problem.id
        )
    )
    next_url = request.form.get("next") or url_for("problems.detail", pid=pid)

    if note:
        db.session.delete(note)
        db.session.commit()
        flash(f"已把「{problem.title}」移出错题本。", "info")
    else:
        db.session.add(MistakeNote(user_id=current_user.id, problem_id=problem.id, content=""))
        db.session.commit()
        flash(f"已把「{problem.title}」加入错题本，记得补上错因和思路。", "success")

    if not next_url.startswith("/"):
        next_url = url_for("problems.detail", pid=pid)
    return redirect(next_url)


@bp.post("/mistakes/<int:pid>/note")
@login_required
def save_note(pid: int):
    problem = db.get_or_404(Problem, pid)
    content = (request.form.get("content") or "").strip()
    if len(content) > 5000:
        flash("笔记太长了（最多 5000 字），请精简一下。", "warning")
        return redirect(url_for("records.mistakes"))

    note = db.session.scalar(
        select(MistakeNote).where(
            MistakeNote.user_id == current_user.id, MistakeNote.problem_id == problem.id
        )
    )
    if not note:
        note = MistakeNote(user_id=current_user.id, problem_id=problem.id, content="")
        db.session.add(note)
    note.content = content
    db.session.commit()
    flash(f"「{problem.title}」的错题笔记已保存。", "success")
    return redirect(url_for("records.mistakes"))


@bp.route("/notes")
@login_required
def notes():
    """所有题目的解题笔记（不限于错题）。"""
    items = db.session.scalars(
        select(ProblemNote)
        .where(ProblemNote.user_id == current_user.id)
        .order_by(ProblemNote.updated_at.desc(), ProblemNote.id.desc())
    ).all()
    last_status = {}
    if items:
        problem_ids = [item.problem_id for item in items]
        rows = db.session.execute(
            select(Submission.problem_id, Submission.status, Submission.created_at)
            .where(
                Submission.user_id == current_user.id,
                Submission.problem_id.in_(problem_ids),
            )
            .order_by(Submission.created_at.asc(), Submission.id.asc())
        ).all()
        for pid, status, _created in rows:
            last_status[pid] = status
    return render_template("records/notes.html", items=items, last_status=last_status)


@bp.post("/notes/<int:pid>/save")
@login_required
def save_problem_note(pid: int):
    problem = db.get_or_404(Problem, pid)
    content = (request.form.get("content") or "").strip()
    next_url = request.form.get("next") or url_for("problems.detail", pid=pid)

    if len(content) > 5000:
        flash("笔记太长了（最多 5000 字），请精简一下。", "warning")
        return redirect(next_url if next_url.startswith("/") else url_for("records.notes"))

    note = db.session.scalar(
        select(ProblemNote).where(
            ProblemNote.user_id == current_user.id, ProblemNote.problem_id == problem.id
        )
    )
    if not content:
        if note:
            db.session.delete(note)
            db.session.commit()
            flash(f"「{problem.title}」的解题笔记已清空。", "info")
        else:
            flash("笔记还是空的，写点思路再保存吧。", "warning")
    else:
        if note is None:
            note = ProblemNote(user_id=current_user.id, problem_id=problem.id, content="")
            db.session.add(note)
        note.content = content
        db.session.commit()
        flash(f"「{problem.title}」的解题笔记已保存。", "success")

    return redirect(next_url if next_url.startswith("/") else url_for("records.notes"))
