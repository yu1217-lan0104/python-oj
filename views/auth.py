"""注册、登录、退出。"""

import re

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_user, logout_user
from sqlalchemy import select

from extensions import db
from models import User

bp = Blueprint("auth", __name__, url_prefix="/auth")

USERNAME_RE = re.compile(r"^[A-Za-z0-9_]{3,20}$")


@bp.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("main.index"))

    if request.method == "POST":
        username = (request.form.get("username") or "").strip()
        nickname = (request.form.get("nickname") or "").strip()
        password = request.form.get("password") or ""
        confirm = request.form.get("confirm") or ""

        errors = []
        if not USERNAME_RE.match(username):
            errors.append("账号需要 3–20 位，只能包含字母、数字和下划线。")
        if len(password) < 6:
            errors.append("密码至少 6 位，建议字母和数字混合。")
        if password != confirm:
            errors.append("两次输入的密码不一致。")
        if len(nickname) > 20:
            errors.append("昵称最多 20 个字符。")
        if not errors and db.session.scalar(select(User).where(User.username == username)):
            errors.append("这个账号已经注册过了，换一个试试。")

        if errors:
            for msg in errors:
                flash(msg, "danger")
            return render_template("auth/register.html", username=username, nickname=nickname), 400

        user = User(username=username, nickname=nickname or username)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        login_user(user)
        flash(f"注册成功，欢迎你，{user.display_name}！先从「入门」题目开始吧。", "success")
        return redirect(url_for("main.index"))

    return render_template("auth/register.html", username="", nickname="")


@bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("main.index"))

    if request.method == "POST":
        username = (request.form.get("username") or "").strip()
        password = request.form.get("password") or ""
        remember = bool(request.form.get("remember"))

        user = db.session.scalar(select(User).where(User.username == username))
        if not user or not user.check_password(password):
            flash("账号或密码不正确，请重新输入。", "danger")
            return render_template("auth/login.html", username=username), 401

        login_user(user, remember=remember)
        flash(f"欢迎回来，{user.display_name}！", "success")
        next_url = request.args.get("next")
        if next_url and next_url.startswith("/"):
            return redirect(next_url)
        return redirect(url_for("main.index"))

    return render_template("auth/login.html", username="")


@bp.route("/logout")
def logout():
    if current_user.is_authenticated:
        logout_user()
        flash("已退出登录，下次记得回来继续练习。", "info")
    return redirect(url_for("main.index"))
