"""给演示账号准备一些真实数据（用于演示 / 截图 / 答辩）。

会以 demo 账号身份提交若干次代码、留下错题笔记，方便直接演示统计与复盘页面。

用法：.venv\\Scripts\\python.exe tools\\seed_demo_activity.py
"""

import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from app import create_app  # noqa: E402
from extensions import db  # noqa: E402
from models import MistakeNote, Problem, ProblemNote, Submission, User  # noqa: E402
from seed_data import PROBLEMS  # noqa: E402

CSRF_RE = re.compile(r'name="_csrf" value="([^"]+)"')

AC_COUNT = 5
WRONG_ATTEMPTS = {
    "两数之和": 'print("1 1")\n',
    "二分查找": "import sys\n\ndata = sys.stdin.read().split()\nn, q = int(data[0]), int(data[1])\na = data[2:2 + n]\nfor x in data[2 + n:]:\n    print(a.index(x) if x in a else -1)\n",
    "括号匹配": "s = input().strip()\nprint('YES' if s.count('(') == s.count(')') else 'NO')\n",
}

NOTES = {
    "两数之和": "一开始写了两重循环，n=1000 时就会超时。正确做法是边遍历边把「数值 → 下标」记到字典里，\n"
    "查 target - x 只要 O(1)。注意下标从 1 开始输出。",
    "括号匹配": "只数左右括号个数是错的，顺序也会影响结果，比如 )( 个数相等但不合法。\n"
    "要用栈：遇到左括号入栈，遇到右括号就和栈顶比较。",
}

STUDY_NOTES = {
    "两数之和": "关键：字典里存的是「已经见过的数 → 下标」。\n"
    "遍历到 x 时只查 target - x，能查到就直接输出，查不到再把 x 存进去，保证不会用到自己。",
    "斐波那契数列": "递归写法直观但 F(40) 要算上亿次；改成从小到大递推，只保留前两项，O(n) 就过了。",
    "二分查找": "模板记牢：while lo <= hi，a[mid] >= x 时往左收缩；题目要第一次出现，所以找到答案后不能立刻返回。",
}


def main() -> int:
    app = create_app()
    app.config.update(TESTING=True)

    with app.app_context():
        user = db.session.query(User).filter_by(username="demo").first()
        if user is None:
            print("演示账号不存在，请先运行：python manage.py demo")
            return 1
        db.session.query(Submission).filter_by(user_id=user.id).delete()
        db.session.query(MistakeNote).filter_by(user_id=user.id).delete()
        db.session.query(ProblemNote).filter_by(user_id=user.id).delete()
        db.session.commit()
        user_id = user.id
        problem_ids = {p.title: p.id for p in db.session.query(Problem).all()}
        titles = [p["title"] for p in PROBLEMS]
        accepted_targets = titles[:AC_COUNT]

    client = app.test_client()
    token = CSRF_RE.search(client.get("/auth/login").get_data(as_text=True)).group(1)
    client.post("/auth/login", data={"username": "demo", "password": "demo123456", "_csrf": token})

    def submit(title: str, code: str) -> None:
        pid = problem_ids[title]
        page = client.get(f"/problems/{pid}")
        tok = CSRF_RE.search(page.get_data(as_text=True)).group(1)
        client.post(f"/problems/{pid}/submit", data={"code": code, "_csrf": tok})

    for item in PROBLEMS:
        if item["title"] in accepted_targets:
            submit(item["title"], item["reference"])

    for title, wrong in WRONG_ATTEMPTS.items():
        if title in problem_ids:
            submit(title, wrong)

    with app.app_context():
        for title, content in NOTES.items():
            pid = problem_ids[title]
            exists = db.session.query(MistakeNote).filter_by(user_id=user_id, problem_id=pid).first()
            if exists is None:
                db.session.add(MistakeNote(user_id=user_id, problem_id=pid, content=content))
        for title, content in STUDY_NOTES.items():
            pid = problem_ids.get(title)
            if pid is None:
                continue
            exists = db.session.query(ProblemNote).filter_by(user_id=user_id, problem_id=pid).first()
            if exists is None:
                db.session.add(ProblemNote(user_id=user_id, problem_id=pid, content=content))
        db.session.commit()
        rows = (
            db.session.query(Submission, Problem)
            .join(Problem, Submission.problem_id == Problem.id)
            .filter(Submission.user_id == user_id)
            .order_by(Submission.id)
            .all()
        )
        for submission, problem in rows:
            print(f"  {submission.status:3} {problem.title}")
        subs = db.session.query(Submission).filter_by(user_id=user_id).count()
        notes = db.session.query(MistakeNote).filter_by(user_id=user_id).count()
        study_notes = db.session.query(ProblemNote).filter_by(user_id=user_id).count()
    print(
        f"完成：{subs} 条提交记录，{notes} 条错题笔记，{study_notes} 篇解题笔记"
        "（账号 demo / demo123456）"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
