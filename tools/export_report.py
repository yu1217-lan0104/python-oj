"""生成一份示例学习报告（Markdown + 独立 HTML），用于检查导出效果 / 答辩演示。

用法：.venv\\Scripts\\python.exe tools\\export_report.py
产物：docs/exports/学习报告_示例.md 与 学习报告_示例.html
"""

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from flask import render_template  # noqa: E402
from sqlalchemy import select  # noqa: E402

from app import create_app  # noqa: E402
from extensions import db  # noqa: E402
from models import User  # noqa: E402
from views.report import build_markdown, build_report  # noqa: E402

OUT_DIR = os.path.join(ROOT, "docs", "exports")


def main() -> int:
    app = create_app()
    os.makedirs(OUT_DIR, exist_ok=True)

    with app.test_request_context("/report"):
        user = db.session.scalar(select(User).where(User.username == "demo"))
        if user is None:
            print("demo 账号不存在，请先运行 manage.py demo")
            return 1
        report = build_report(user.id)
        markdown = build_markdown(report, user)
        html = render_template("report/export.html", report=report, user=user)

    md_path = os.path.join(OUT_DIR, "学习报告_示例.md")
    html_path = os.path.join(OUT_DIR, "学习报告_示例.html")
    with open(md_path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(markdown)
    with open(html_path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(html)

    print(f"已生成：{md_path}")
    print(f"已生成：{html_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
