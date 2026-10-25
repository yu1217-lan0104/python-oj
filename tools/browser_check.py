"""浏览器端自检：验证「代码草稿自动保存」在真实 Chrome 里的行为。

为什么单独写这个脚本：草稿逻辑跑在浏览器里，Flask 的测试客户端测不到，
所以这里用 Chrome DevTools Protocol 驱动无头 Chrome，真的去输入、刷新、读 localStorage。

前置：先启动站点（python app.py），依赖：websocket-client（仅开发期用）。

用法：.venv\\Scripts\\python.exe tools\\browser_check.py
"""

import json
import os
import subprocess
import sys
import time
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

import websocket  # noqa: E402
from flask.sessions import SecureCookieSessionInterface  # noqa: E402
from sqlalchemy import select  # noqa: E402

from app import create_app  # noqa: E402
from extensions import db  # noqa: E402
from models import Problem, User  # noqa: E402

CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
DEBUG_PORT = 9333
BASE_URL = "http://127.0.0.1:5000"
PROFILE = os.path.join(ROOT, ".shotcache", "cdp-profile")

failures = []


def check(name, condition, detail=""):
    if condition:
        print(f"  [PASS] {name}")
    else:
        failures.append(name)
        print(f"  [FAIL] {name} {detail}")


class CDP:
    def __init__(self, url):
        self.ws = websocket.create_connection(url, timeout=15, suppress_origin=True)
        self.next_id = 0
        self.events = []

    def send(self, method, **params):
        self.next_id += 1
        self.ws.send(json.dumps({"id": self.next_id, "method": method, "params": params}))
        while True:
            message = json.loads(self.ws.recv())
            if message.get("id") == self.next_id:
                if "error" in message:
                    raise RuntimeError(f"{method} 失败：{message['error']}")
                return message.get("result", {})
            self.events.append(message)

    def evaluate(self, expression):
        result = self.send(
            "Runtime.evaluate",
            expression=expression,
            returnByValue=True,
            awaitPromise=True,
        )
        return result.get("result", {}).get("value")

    def close(self):
        try:
            self.ws.close()
        except Exception:  # noqa: BLE001
            pass


def wait_ready(cdp: CDP, timeout=15.0):
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            if cdp.evaluate("document.readyState") == "complete":
                return True
        except Exception:  # noqa: BLE001
            pass
        time.sleep(0.2)
    return False


def main() -> int:
    app = create_app()

    with app.app_context():
        user = db.session.scalar(select(User).where(User.username == "demo"))
        if user is None:
            print("demo 账号不存在，请先运行 manage.py demo")
            return 1
        problem = db.session.scalar(select(Problem).order_by(Problem.id))
        problem_id = problem.id
        cookie = SecureCookieSessionInterface().get_signing_serializer(app).dumps(
            {"_user_id": str(user.id), "_fresh": True, "_id": "cdp-check", "_csrf": "cdp"}
        )

    os.makedirs(PROFILE, exist_ok=True)
    chrome = subprocess.Popen(
        [
            CHROME,
            "--headless=new",
            "--no-sandbox",
            "--disable-gpu",
            "--disable-breakpad",
            "--disable-crash-reporter",
            "--no-first-run",
            "--remote-allow-origins=*",
            f"--remote-debugging-port={DEBUG_PORT}",
            f"--user-data-dir={PROFILE}",
            "about:blank",
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    cdp = None
    try:
        for _ in range(50):
            try:
                with urllib.request.urlopen(f"http://127.0.0.1:{DEBUG_PORT}/json/list", timeout=2) as resp:
                    targets = json.load(resp)
                page = next(t for t in targets if t["type"] == "page")
                break
            except Exception:  # noqa: BLE001
                time.sleep(0.3)
        else:
            raise SystemExit("Chrome 调试端口没有起来")

        cdp = CDP(page["webSocketDebuggerUrl"])
        cdp.send("Page.enable")
        cdp.send("Runtime.enable")
        cdp.send("Network.enable")
        cdp.send(
            "Network.setCookie",
            name="session",
            value=cookie,
            domain="127.0.0.1",
            path="/",
        )

        print("① 打开题目页（已注入登录态）")
        cdp.send("Page.navigate", url=f"{BASE_URL}/problems/{problem_id}")
        check("页面加载完成", wait_ready(cdp))
        check("编辑器存在", cdp.evaluate("!!document.querySelector('#code')") is True)
        check("草稿提示存在", cdp.evaluate("!!document.querySelector('#draft-hint')") is True)

        print("② 输入代码后自动保存草稿")
        cdp.evaluate(
            "(() => { const e = document.querySelector('#code');"
            "e.value = 'print(6 * 7)';"
            "e.dispatchEvent(new Event('input', {bubbles: true})); return true; })()"
        )
        time.sleep(1.0)
        draft = cdp.evaluate(f"localStorage.getItem('pyoj:draft:{problem_id}')")
        check("localStorage 写入草稿", bool(draft), str(draft))
        check("草稿内容包括输入的代码", "print(6 * 7)" in (draft or ""))

        print("③ 刷新页面后自动恢复")
        cdp.send("Page.reload", ignoreCache=True)
        check("重新加载完成", wait_ready(cdp))
        time.sleep(0.6)
        check("输入框恢复为草稿内容", cdp.evaluate("document.querySelector('#code').value") == "print(6 * 7)")
        hint = cdp.evaluate("document.querySelector('#draft-hint').textContent") or ""
        check("提示显示已恢复草稿", "恢复" in hint, hint)

        print("④ 清空草稿")
        cdp.evaluate("document.querySelector('#clear-draft').click()")
        time.sleep(0.4)
        check(
            "localStorage 已清空",
            cdp.evaluate(f"localStorage.getItem('pyoj:draft:{problem_id}')") is None,
        )
        check(
            "输入框恢复默认模板",
            cdp.evaluate("document.querySelector('#code').value") == cdp.evaluate(
                "document.querySelector('#code').dataset.default"
            ),
        )

        print("⑤ 页面无 JS 报错")
        errors = [e for e in cdp.events if e.get("method") == "Runtime.exceptionThrown"]
        check("没有未捕获异常", not errors, str(errors[:1]))
    finally:
        if cdp:
            cdp.close()
        chrome.terminate()
        try:
            chrome.wait(timeout=10)
        except subprocess.TimeoutExpired:
            chrome.kill()

    print()
    if failures:
        print(f"有 {len(failures)} 项失败：{failures}")
        return 1
    print("浏览器端草稿功能自检通过 ✅")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
