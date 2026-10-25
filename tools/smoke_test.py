"""端到端冒烟测试：注册登录 → 浏览题库 → 提交判题 → 错题本 → 统计页。

用法：.venv\\Scripts\\python.exe tools\\smoke_test.py
需要一个可写的本地数据库（默认 pyoj.db，测试会创建 testsmoke 账号）。
"""

import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from app import create_app  # noqa: E402
from extensions import db  # noqa: E402
from models import MistakeNote, Problem, ProblemNote, Submission, Topic, User  # noqa: E402

CSRF_RE = re.compile(r'name="_csrf" value="([^"]+)"')
failures = []


def check(name: str, condition: bool, detail: str = "") -> None:
    if condition:
        print(f"  [PASS] {name}")
    else:
        failures.append(name)
        print(f"  [FAIL] {name} {detail}")


def get_csrf(client, path: str) -> str:
    resp = client.get(path)
    match = CSRF_RE.search(resp.get_data(as_text=True))
    assert match, f"{path} 页面没有 CSRF token"
    return match.group(1)


def main() -> int:
    app = create_app()
    app.config.update(TESTING=True)

    with app.app_context():
        user = User.query.filter_by(username="testsmoke").first()
        if user is None:
            user = User(username="testsmoke", nickname="冒烟测试")
            user.set_password("test123456")
            db.session.add(user)
        else:
            db.session.query(Submission).filter_by(user_id=user.id).delete()
            db.session.query(MistakeNote).filter_by(user_id=user.id).delete()
            db.session.query(ProblemNote).filter_by(user_id=user.id).delete()
        db.session.commit()
        user_id = user.id
        problem = Problem.query.order_by(Problem.id).first()
        problem_id, problem_title = problem.id, problem.title

    client = app.test_client()

    print("① 页面可访问性")
    for path in ("/", "/problems/", "/problems/?difficulty=入门", "/problems/?tag=二分", "/auth/login", "/auth/register"):
        resp = client.get(path)
        check(f"GET {path} -> {resp.status_code}", resp.status_code == 200)

    print("② 登录")
    token = get_csrf(client, "/auth/login")
    resp = client.post(
        "/auth/login",
        data={"username": "testsmoke", "password": "test123456", "_csrf": token},
        follow_redirects=True,
    )
    check("登录成功", resp.status_code == 200 and "冒烟测试" in resp.get_data(as_text=True))

    print("③ 题目详情")
    resp = client.get(f"/problems/{problem_id}")
    body = resp.get_data(as_text=True)
    check("题目页 200", resp.status_code == 200)
    check("题目页含标题", problem_title in body)
    check("题目页含提交编辑器", 'id="code"' in body)

    def submit(code: str, follow: bool = True):
        tok = get_csrf(client, f"/problems/{problem_id}")
        return client.post(
            f"/problems/{problem_id}/submit",
            data={"code": code, "_csrf": tok},
            follow_redirects=follow,
        )

    print("④ 判题：AC")
    accepted = "n, t = map(int, input().split())\nnu = list(map(int, input().split()))\nseen = {}\nfor i, x in enumerate(nu):\n    if t - x in seen:\n        print(seen[t - x] + 1, i + 1)\n        break\n    seen[x] = i\n"
    resp = submit(accepted)
    body = resp.get_data(as_text=True)
    check("AC 提交成功", resp.status_code == 200 and "通过" in body)

    print("⑤ 判题：WA")
    resp = submit('print("0 0")\n')
    body = resp.get_data(as_text=True)
    check("WA 被识别", "答案错误" in body or "WA" in body)

    print("⑥ 判题：CE（语法错误）")
    resp = submit("for i in range(3)\n    print(i)\n")
    body = resp.get_data(as_text=True)
    check("CE 被识别", "CE" in body and "语法错误" in body)

    print("⑦ 判题：RE（运行时错误）")
    resp = submit("a = []\nprint(a[3])\n")
    body = resp.get_data(as_text=True)
    check("RE 被识别", "RE" in body and "IndexError" in body)

    print("⑧ 判题：TLE（死循环）")
    resp = submit("while True:\n    pass\n")
    body = resp.get_data(as_text=True)
    check("TLE 被识别", "TLE" in body and "超时" in body)

    print("⑨ 提交记录与详情")
    resp = client.get("/submissions")
    check("提交记录页", resp.status_code == 200 and problem_title in resp.get_data(as_text=True))

    with app.app_context():
        sub = (
            Submission.query.filter_by(user_id=user_id, status="AC")
            .order_by(Submission.id.desc())
            .first()
        )
        sub_id = sub.id if sub else 0
    resp = client.get(f"/submissions/{sub_id}")
    body = resp.get_data(as_text=True)
    check("提交详情页", resp.status_code == 200 and "判题信息" in body and "提交的代码" in body)

    print("⑩ 错题本")
    tok = get_csrf(client, f"/problems/{problem_id}")
    resp = client.post(
        f"/mistakes/{problem_id}/toggle",
        data={"_csrf": tok, "next": "/mistakes"},
        follow_redirects=True,
    )
    body = resp.get_data(as_text=True)
    check("加入错题本", resp.status_code == 200 and problem_title in body)

    tok = get_csrf(client, "/mistakes")
    resp = client.post(
        f"/mistakes/{problem_id}/note",
        data={"_csrf": tok, "content": "哈希表要边遍历边记录，别忘了下标从 1 开始。"},
        follow_redirects=True,
    )
    check("保存错题笔记", resp.status_code == 200 and "哈希表要边遍历边记录" in resp.get_data(as_text=True))

    print("⑪ 个人中心与统计")
    resp = client.get("/profile")
    body = resp.get_data(as_text=True)
    check("个人中心页", resp.status_code == 200 and "通过率" in body and "难度进度" in body)
    check("统计到已完成题量", "已完成题量" in body)

    print("⑫ 未登录保护")
    anon = app.test_client()
    resp = anon.get("/profile", follow_redirects=False)
    check("未登录访问个人中心被重定向", resp.status_code == 302)

    print("⑬ 专题训练")
    resp = client.get("/topics")
    body = resp.get_data(as_text=True)
    check("专题列表页", resp.status_code == 200 and "专题训练" in body and "哈希表入门" in body)

    with app.app_context():
        topic_id = db.session.scalar(db.select(Topic.id).order_by(Topic.id))
    resp = client.get(f"/topics/{topic_id}")
    body = resp.get_data(as_text=True)
    check("专题详情页", resp.status_code == 200 and "开始" in body and "已通过" in body)

    print("⑭ 语法卡片")
    resp = client.get("/cards")
    body = resp.get_data(as_text=True)
    check("卡片列表页", resp.status_code == 200 and "语法卡片" in body and "21 张" in body)
    resp = client.get("/cards?category=易错点")
    check("卡片分类筛选", resp.status_code == 200 and "差一错误" in resp.get_data(as_text=True))
    resp = client.get("/cards?keyword=二分")
    check("卡片搜索", resp.status_code == 200 and "二分" in resp.get_data(as_text=True))

    print("⑮ 解题笔记")
    tok = get_csrf(client, f"/problems/{problem_id}")
    resp = client.post(
        f"/notes/{problem_id}/save",
        data={"_csrf": tok, "content": "思路：边遍历边用字典记录，查 target - x。"},
        follow_redirects=True,
    )
    check("保存解题笔记", resp.status_code == 200 and "解题笔记已保存" in resp.get_data(as_text=True))
    resp = client.get("/notes")
    check("笔记列表页", resp.status_code == 200 and "查 target - x" in resp.get_data(as_text=True))
    resp = client.get(f"/problems/{problem_id}")
    check("题目页回填笔记", "查 target - x" in resp.get_data(as_text=True))

    print("⑯ 学习报告与图表")
    resp = client.get("/report")
    body = resp.get_data(as_text=True)
    check("报告页", resp.status_code == 200 and "学习报告" in body and "学习建议" in body)
    check("报告含 SVG 图表", body.count("<svg") >= 3)
    resp = client.get("/report/export?format=md")
    body = resp.get_data(as_text=True)
    check(
        "导出 Markdown",
        resp.status_code == 200 and "# Python 算法学习报告" in body and "## 四、学习建议" in body,
    )
    resp = client.get("/report/export?format=html")
    body = resp.get_data(as_text=True)
    check(
        "导出 HTML（自带图表）",
        resp.status_code == 200 and "<svg" in body and "学习建议" in body,
    )

    print()
    if failures:
        print(f"共 {len(failures)} 项失败：{failures}")
        return 1
    print("全部冒烟测试通过 ✅")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

