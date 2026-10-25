"""命令行工具：建库、建表、导入题库/专题/卡片、创建演示账号。

常用命令（在项目根目录执行）：

    .venv\\Scripts\\python.exe manage.py init         # 建库 + 建表 + 导入题库/专题/卡片
    .venv\\Scripts\\python.exe manage.py seed         # 只导入/更新题库
    .venv\\Scripts\\python.exe manage.py topics       # 重新导入专题套题
    .venv\\Scripts\\python.exe manage.py cards        # 重新导入语法卡片
    .venv\\Scripts\\python.exe manage.py demo         # 创建演示账号 demo / demo123456
    .venv\\Scripts\\python.exe manage.py reset-user   # 清空演示账号的提交、错题与笔记
    .venv\\Scripts\\python.exe manage.py db-check     # 打印当前数据库连接
"""

import argparse
import sys

from sqlalchemy import create_engine, select, text
from sqlalchemy.engine import make_url

from app import create_app
from cards_data import CARDS
from config import database_name
from extensions import db
from models import Card, MistakeNote, Problem, ProblemNote, Submission, Topic, User
from seed_data import PROBLEMS
from topics_data import TOPICS

DEMO_USERNAME = "demo"
DEMO_PASSWORD = "demo123456"


def ensure_mysql_database(uri: str) -> None:
    """MySQL 下先建库（SQLite 不需要，直接跳过）。"""
    if not uri.startswith("mysql"):
        return
    url = make_url(uri)
    database = url.database
    server_url = url.set(database=None)
    engine = create_engine(server_url, isolation_level="AUTOCOMMIT")
    with engine.connect() as conn:
        conn.execute(
            text(
                f"CREATE DATABASE IF NOT EXISTS `{database}` "
                "DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
            )
        )
    engine.dispose()
    print(f"[建库] 已确认数据库 {database} 存在")


def cmd_init(_args) -> None:
    app = create_app()
    uri = app.config["SQLALCHEMY_DATABASE_URI"]
    print(f"[数据库] {database_name(uri)}")
    ensure_mysql_database(uri)
    with app.app_context():
        db.create_all()
        print("[建表] user / problem / submit / mistake_note / topic / problem_note / card 已就绪")
    cmd_seed(_args)
    cmd_topics(_args)
    cmd_cards(_args)


def cmd_seed(_args) -> None:
    app = create_app()
    with app.app_context():
        created, updated = 0, 0
        for item in PROBLEMS:
            problem = db.session.scalar(select(Problem).where(Problem.title == item["title"]))
            tests = item["tests"]
            sample = tests[0]
            if problem is None:
                problem = Problem(title=item["title"])
                db.session.add(problem)
                created += 1
            else:
                updated += 1
            problem.difficulty = item["difficulty"]
            problem.tags = item["tags"]
            problem.description = item["description"]
            problem.hint = item["hint"]
            problem.sample_input = sample["input"]
            problem.sample_output = sample["output"]
            problem.set_tests(tests)
            problem.time_limit_ms = 2000
        db.session.commit()
        total = db.session.scalar(select(db.func.count(Problem.id)))
        print(f"[题库] 新增 {created} 题，更新 {updated} 题，当前共 {total} 题")


def cmd_topics(_args) -> None:
    """按 topics_data.TOPICS 重建专题套题（题目按标题关联）。"""
    app = create_app()
    with app.app_context():
        from models import topic_problem

        db.session.execute(db.delete(topic_problem))
        db.session.execute(db.delete(Topic))
        db.session.commit()

        problems = {p.title: p for p in db.session.scalars(select(Problem)).all()}
        missing = []
        for order, item in enumerate(TOPICS, start=1):
            topic = Topic(
                name=item["name"],
                slug=item["slug"],
                icon=item.get("icon", "📘"),
                description=item.get("description", ""),
                sort_order=order,
            )
            db.session.add(topic)
            db.session.flush()
            for position, title in enumerate(item["problems"], start=1):
                problem = problems.get(title)
                if problem is None:
                    missing.append(title)
                    continue
                db.session.execute(
                    topic_problem.insert().values(
                        topic_id=topic.id, problem_id=problem.id, position=position
                    )
                )
        db.session.commit()
        print(f"[专题] 已导入 {len(TOPICS)} 个专题")
        if missing:
            print(f"[专题] 警告：以下题目不存在，已跳过：{'、'.join(sorted(set(missing)))}")


def cmd_cards(_args) -> None:
    """重建 Python 语法卡片。"""
    app = create_app()
    with app.app_context():
        db.session.execute(db.delete(Card))
        db.session.commit()
        for order, item in enumerate(CARDS, start=1):
            db.session.add(
                Card(
                    title=item["title"],
                    category=item["category"],
                    summary=item.get("summary", ""),
                    content=item["content"],
                    tags=item.get("tags", ""),
                    sort_order=order,
                )
            )
        db.session.commit()
        categories = sorted({item["category"] for item in CARDS})
        print(f"[卡片] 已导入 {len(CARDS)} 张卡片，分类：{'、'.join(categories)}")


def cmd_demo(_args) -> None:
    app = create_app()
    with app.app_context():
        user = db.session.scalar(select(User).where(User.username == DEMO_USERNAME))
        if user is None:
            user = User(username=DEMO_USERNAME, nickname="演示同学")
            user.set_password(DEMO_PASSWORD)
            db.session.add(user)
            db.session.commit()
            print(f"[演示账号] 已创建 {DEMO_USERNAME} / {DEMO_PASSWORD}")
        else:
            print(f"[演示账号] {DEMO_USERNAME} 已存在，密码未改动")


def cmd_reset_user(_args) -> None:
    app = create_app()
    with app.app_context():
        user = db.session.scalar(select(User).where(User.username == DEMO_USERNAME))
        if user is None:
            print(f"[演示账号] 不存在 {DEMO_USERNAME}")
            return
        db.session.execute(
            db.delete(Submission).where(Submission.user_id == user.id)
        )
        db.session.execute(
            db.delete(MistakeNote).where(MistakeNote.user_id == user.id)
        )
        db.session.execute(
            db.delete(ProblemNote).where(ProblemNote.user_id == user.id)
        )
        db.session.commit()
        print("[演示账号] 已清空该账号的提交记录、错题本与解题笔记")


def cmd_db_check(_args) -> None:
    app = create_app()
    uri = app.config["SQLALCHEMY_DATABASE_URI"]
    print(f"[数据库] {database_name(uri)}")
    with app.app_context():
        try:
            problems = db.session.scalar(select(db.func.count(Problem.id)))
            users = db.session.scalar(select(db.func.count(User.id)))
            subs = db.session.scalar(select(db.func.count(Submission.id)))
            topics = db.session.scalar(select(db.func.count(Topic.id)))
            cards = db.session.scalar(select(db.func.count(Card.id)))
            notes = db.session.scalar(select(db.func.count(ProblemNote.id)))
            print(
                f"[统计] 用户 {users} · 题目 {problems} · 提交 {subs} "
                f"· 专题 {topics} · 卡片 {cards} · 解题笔记 {notes}"
            )
        except Exception as exc:  # noqa: BLE001
            print(f"[错误] 数据库连接或表结构有问题：{exc}")
            sys.exit(1)


COMMANDS = {
    "init": cmd_init,
    "seed": cmd_seed,
    "topics": cmd_topics,
    "cards": cmd_cards,
    "demo": cmd_demo,
    "reset-user": cmd_reset_user,
    "db-check": cmd_db_check,
}


def main() -> None:
    parser = argparse.ArgumentParser(description="Python 算法练习场 管理工具")
    parser.add_argument("command", choices=sorted(COMMANDS), help="要执行的命令")
    args = parser.parse_args()
    COMMANDS[args.command](args)


if __name__ == "__main__":
    main()
