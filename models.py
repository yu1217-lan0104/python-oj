"""数据模型：user / problem / submit / mistake_note 四张表。"""

import json
from datetime import datetime

from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash

from extensions import db, login_manager


class User(UserMixin, db.Model):
    __tablename__ = "user"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    nickname = db.Column(db.String(64), nullable=False, default="")
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.now)

    def set_password(self, raw: str) -> None:
        self.password_hash = generate_password_hash(raw)

    def check_password(self, raw: str) -> bool:
        return check_password_hash(self.password_hash, raw)

    @property
    def display_name(self) -> str:
        return self.nickname or self.username

    def __repr__(self) -> str:  # pragma: no cover
        return f"<User {self.username}>"


@login_manager.user_loader
def load_user(user_id: str):
    return db.session.get(User, int(user_id))


class Problem(db.Model):
    __tablename__ = "problem"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(128), nullable=False)
    difficulty = db.Column(db.String(16), nullable=False, default="入门", index=True)
    tags = db.Column(db.String(255), nullable=False, default="")
    description = db.Column(db.Text, nullable=False, default="")
    hint = db.Column(db.Text, nullable=False, default="")
    sample_input = db.Column(db.Text, nullable=False, default="")
    sample_output = db.Column(db.Text, nullable=False, default="")
    tests_json = db.Column(db.Text, nullable=False, default="[]")
    time_limit_ms = db.Column(db.Integer, nullable=False, default=2000)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.now)

    @property
    def tag_list(self):
        return [t for t in (self.tags or "").split(",") if t]

    @property
    def tests(self):
        try:
            return json.loads(self.tests_json or "[]")
        except json.JSONDecodeError:
            return []

    def set_tests(self, tests) -> None:
        self.tests_json = json.dumps(tests, ensure_ascii=False)

    @property
    def difficulty_class(self) -> str:
        return {"入门": "easy", "基础": "normal"}.get(self.difficulty, "normal")

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Problem {self.id} {self.title}>"


class Submission(db.Model):
    __tablename__ = "submit"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, index=True)
    problem_id = db.Column(db.Integer, db.ForeignKey("problem.id"), nullable=False, index=True)
    code = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(8), nullable=False, default="WA", index=True)
    passed = db.Column(db.Integer, nullable=False, default=0)
    total = db.Column(db.Integer, nullable=False, default=0)
    time_ms = db.Column(db.Integer, nullable=False, default=0)
    message = db.Column(db.Text, nullable=False, default="")
    detail_json = db.Column(db.Text, nullable=False, default="[]")
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.now, index=True)

    user = db.relationship("User", backref=db.backref("submissions", lazy="dynamic"))
    problem = db.relationship("Problem", backref=db.backref("submissions", lazy="dynamic"))

    @property
    def is_accepted(self) -> bool:
        return self.status == "AC"

    @property
    def status_text(self) -> str:
        return STATUS_TEXT.get(self.status, self.status)

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Submission {self.id} {self.status}>"


class MistakeNote(db.Model):
    __tablename__ = "mistake_note"
    __table_args__ = (db.UniqueConstraint("user_id", "problem_id", name="uq_mistake_user_problem"),)

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, index=True)
    problem_id = db.Column(db.Integer, db.ForeignKey("problem.id"), nullable=False, index=True)
    content = db.Column(db.Text, nullable=False, default="")
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.now)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)

    user = db.relationship("User", backref=db.backref("mistake_notes", lazy="dynamic"))
    problem = db.relationship("Problem", backref=db.backref("mistake_notes", lazy="dynamic"))

    def __repr__(self) -> str:  # pragma: no cover
        return f"<MistakeNote u{self.user_id} p{self.problem_id}>"


topic_problem = db.Table(
    "topic_problem",
    db.Column("topic_id", db.Integer, db.ForeignKey("topic.id", ondelete="CASCADE"), primary_key=True),
    db.Column(
        "problem_id", db.Integer, db.ForeignKey("problem.id", ondelete="CASCADE"), primary_key=True
    ),
    db.Column("position", db.Integer, nullable=False, default=0),
)


class Topic(db.Model):
    """专题训练套题：把若干题目按训练顺序编成一组。"""

    __tablename__ = "topic"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), nullable=False)
    slug = db.Column(db.String(64), unique=True, nullable=False)
    description = db.Column(db.String(255), nullable=False, default="")
    icon = db.Column(db.String(8), nullable=False, default="📘")
    sort_order = db.Column(db.Integer, nullable=False, default=0)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.now)

    problems = db.relationship(
        "Problem",
        secondary=topic_problem,
        lazy="selectin",
        order_by="topic_problem.c.position",
        backref=db.backref("topics", lazy="dynamic"),
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Topic {self.name}>"


class ProblemNote(db.Model):
    """自定义解题笔记：任意题目都可以写思路，不限于错题。"""

    __tablename__ = "problem_note"
    __table_args__ = (
        db.UniqueConstraint("user_id", "problem_id", name="uq_problem_note_user_problem"),
    )

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, index=True)
    problem_id = db.Column(db.Integer, db.ForeignKey("problem.id"), nullable=False, index=True)
    content = db.Column(db.Text, nullable=False, default="")
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.now)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)

    user = db.relationship("User", backref=db.backref("problem_notes", lazy="dynamic"))
    problem = db.relationship("Problem", backref=db.backref("problem_notes", lazy="dynamic"))

    def __repr__(self) -> str:  # pragma: no cover
        return f"<ProblemNote u{self.user_id} p{self.problem_id}>"


class Card(db.Model):
    """Python 语法 / 算法知识点卡片。"""

    __tablename__ = "card"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(64), nullable=False)
    category = db.Column(db.String(32), nullable=False, default="基础语法", index=True)
    summary = db.Column(db.String(200), nullable=False, default="")
    content = db.Column(db.Text, nullable=False, default="")
    tags = db.Column(db.String(128), nullable=False, default="")
    sort_order = db.Column(db.Integer, nullable=False, default=0)

    @property
    def tag_list(self):
        return [t for t in (self.tags or "").split(",") if t]

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Card {self.title}>"


STATUS_TEXT = {
    "AC": "通过",
    "WA": "答案错误",
    "TLE": "运行超时",
    "RE": "运行出错",
    "CE": "语法错误",
    "SE": "评测异常",
}

STATUS_COLOR = {
    "AC": "success",
    "WA": "danger",
    "TLE": "warning",
    "RE": "orange",
    "CE": "purple",
    "SE": "secondary",
}

DIFFICULTIES = ["入门", "基础"]
