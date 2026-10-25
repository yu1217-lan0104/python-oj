"""生成演示截图（答辩 / README 用）。

做法：用 Flask 的会话签名器直接构造 demo 账号的 session cookie，然后启动一个
只在本机转发的代理，把 cookie 注入到每个请求里，最后用无头 Chrome 截图。
这样不用改动应用代码，也不需要人工登录。

前置：先启动站点（python app.py），并准备好 demo 账号数据
      （manage.py demo + tools/seed_demo_activity.py）。

用法：.venv\\Scripts\\python.exe tools\\make_screenshots.py
"""

import http.server
import os
import shutil
import socket
import subprocess
import sys
import tempfile
import threading
import urllib.error
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from flask.sessions import SecureCookieSessionInterface  # noqa: E402
from sqlalchemy import select  # noqa: E402

from app import create_app  # noqa: E402
from extensions import db  # noqa: E402
from models import Problem, Submission, Topic, User  # noqa: E402

BACKEND = "http://127.0.0.1:5000"
PROXY_PORT = 5055
OUT_DIR = os.path.join(ROOT, "docs", "screenshots")
CHROME_CANDIDATES = [
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
]

PAGES = [
    ("01-home-guest.png", "/", 1500, False),
    ("02-home.png", "/", 1600, True),
    ("03-problems.png", "/problems/", 1320, True),
    ("04-problem.png", "/problems/{problem_id}", 1450, True),
    ("05-submission-ac.png", "/submissions/{ac_id}", 1500, True),
    ("06-mistakes.png", "/mistakes", 1120, True),
    ("07-profile.png", "/profile", 1500, True),
    ("08-register.png", "/auth/register", 1000, False),
    ("09-topics.png", "/topics", 1150, True),
    ("10-topic-detail.png", "/topics/{topic_id}", 1000, True),
    ("11-cards.png", "/cards", 1750, True),
    ("12-notes.png", "/notes", 1100, True),
    ("13-report.png", "/report", 2800, True),
]


def build_cookie(app) -> str:
    with app.app_context():
        user = db.session.scalar(select(User).where(User.username == "demo"))
        if user is None:
            raise SystemExit("demo 账号不存在，请先运行 manage.py demo")
        user_id = user.id
    serializer = SecureCookieSessionInterface().get_signing_serializer(app)
    return serializer.dumps(
        {"_user_id": str(user_id), "_fresh": True, "_id": "screenshot-session", "_csrf": "screenshot"}
    )


def make_proxy(cookie: str):
    class Handler(http.server.BaseHTTPRequestHandler):
        def do_GET(self):  # noqa: N802
            request = urllib.request.Request(
                BACKEND + self.path, headers={"Cookie": f"session={cookie}", "Accept-Language": "zh-CN"}
            )
            try:
                with urllib.request.urlopen(request, timeout=20) as resp:
                    body, status, headers = resp.read(), resp.status, resp.headers
            except urllib.error.HTTPError as exc:
                body, status, headers = exc.read(), exc.code, exc.headers
            self.send_response(status)
            for key, value in headers.items():
                if key.lower() in ("content-length", "transfer-encoding", "connection"):
                    continue
                self.send_header(key, value)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, *args):
            return

    server = http.server.ThreadingHTTPServer(("127.0.0.1", PROXY_PORT), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return server


def find_chrome() -> str:
    for path in CHROME_CANDIDATES:
        if os.path.exists(path):
            return path
    raise SystemExit("没有找到 Chrome / Edge，无法截图")


def wait_backend(timeout: float = 20.0) -> None:
    import time

    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with socket.create_connection(("127.0.0.1", 5000), timeout=1):
                return
        except OSError:
            time.sleep(0.4)
    raise SystemExit("检测不到 127.0.0.1:5000，请先运行 python app.py")


def shoot(chrome: str, url: str, out_path: str, height: int, tmpdir: str) -> None:
    target = os.path.join(tmpdir, os.path.basename(out_path))
    profile = os.path.join(tmpdir, "profile-" + os.path.splitext(os.path.basename(out_path))[0])
    args = [
        "--headless=new",
        "--no-sandbox",
        "--disable-gpu",
        "--disable-breakpad",
        "--disable-crash-reporter",
        "--no-first-run",
        "--no-default-browser-check",
        "--hide-scrollbars",
        "--force-device-scale-factor=1",
        f"--window-size=1360,{height}",
        "--virtual-time-budget=6000",
        "--user-data-dir=" + profile,
        "--screenshot=" + target,
        url,
    ]
    proc = subprocess.run([chrome] + args, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=120)
    if not os.path.exists(target):
        raise SystemExit(f"截图失败（Chrome 退出码 {proc.returncode}）：{url}")
    shutil.copyfile(target, out_path)


def main() -> int:
    app = create_app()
    wait_backend()
    cookie = build_cookie(app)
    server = make_proxy(cookie)
    chrome = find_chrome()
    os.makedirs(OUT_DIR, exist_ok=True)
    os.makedirs(os.path.join(ROOT, ".shotcache"), exist_ok=True)

    with app.app_context():
        ac_id = (
            db.session.scalar(
                select(Submission.id)
                .where(Submission.status == "AC")
                .order_by(Submission.id.desc())
            )
            or 1
        )
        first_problem = db.session.scalar(select(Problem).order_by(Problem.id.asc()))
        first_id = first_problem.id if first_problem else 1
        first_topic = db.session.scalar(select(Topic).order_by(Topic.sort_order.asc(), Topic.id.asc()))
        topic_id = first_topic.id if first_topic else 1

    try:
        for name, path, height, need_login in PAGES:
            url_path = path.format(ac_id=ac_id, problem_id=first_id, topic_id=topic_id)
            url = (
                f"http://127.0.0.1:{PROXY_PORT}{url_path}" if need_login else BACKEND + url_path
            )
            out_path = os.path.join(OUT_DIR, name)
            with tempfile.TemporaryDirectory(prefix="shot_", dir=os.path.join(ROOT, ".shotcache")) as tmpdir:
                shoot(chrome, url, out_path, height, tmpdir)
            print(f"  ✓ {name}")
    finally:
        server.shutdown()

    print(f"截图已保存到 {OUT_DIR}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
