"""本地评测模块：调用本机 Python3 解释器运行用户代码，逐个测试点比对输出。

返回结果保持新手可读：
    AC  全部测试点通过
    WA  输出与标准答案不一致
    TLE 某个测试点运行超时（通常是死循环）
    RE  程序抛出了异常（附带异常类型、行号和改进建议）
    CE  代码本身有语法错误 / 使用了评测环境禁止的模块

说明：这是一个"本地判题器"，不是安全沙箱。按策划书约定，系统只在本机
127.0.0.1 使用，禁止部署到公网。
"""

import ast
import os
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass, field

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RUNNER = os.path.join(BASE_DIR, "judge_runner.py")

FORBIDDEN_MODULES = {
    "os",
    "shutil",
    "subprocess",
    "socket",
    "ctypes",
    "multiprocessing",
    "signal",
    "winreg",
    "pty",
    "http",
    "urllib",
    "requests",
}

ERROR_TIPS = {
    "IndexError": "下标越界：访问了列表中不存在的位置。索引从 0 开始，长度为 n 的列表最大下标是 n-1。",
    "KeyError": "字典里没有这个键：可以先用 `in` 判断，或者用 dict.get(key, 默认值)。",
    "ValueError": "数据格式不对（例如 int('12a')）。检查输入按题目格式解析，必要时先 strip()。",
    "ZeroDivisionError": "除数为 0：检查分母是否可能为 0，考虑加一个 if 判断。",
    "NameError": "变量名未定义：检查拼写，或确认变量在使用前已经赋值。",
    "TypeError": "类型不匹配（例如字符串和整数直接相加）。需要转换时用 int() / str()。",
    "RecursionError": "递归层数过深：检查递归出口是否正确，题目一般不需要超过 1000 层递归。",
    "ModuleNotFoundError": "评测环境只有 Python 标准库，不能使用第三方库。",
    "ImportError": "评测环境只有 Python 标准库，不能使用第三方库。",
    "IndentationError": "缩进不一致：同一代码块请统一使用 4 个空格，不要混用 Tab。",
    "TabError": "缩进中混用了 Tab 和空格，建议全部改成 4 个空格。",
    "SyntaxError": "语法错误：检查括号、冒号、引号是否成对，`if`/`for` 行末是否缺少冒号。",
    "EOFError": "读取输入时数据已结束：检查是否多读了一次 input()，或输入格式是否按题目要求。",
    "AttributeError": "对象没有该属性：检查变量类型，例如列表不能用 strip()。",
    "UnboundLocalError": "变量在赋值前被使用：检查函数内是否先读取了尚未赋值的局部变量。",
    "MemoryError": "内存不足：检查是否无限制地往列表里追加数据。",
    "StopIteration": "迭代器已经取完：检查 next() 的使用位置。",
}

STATUS_AC = "AC"
STATUS_WA = "WA"
STATUS_TLE = "TLE"
STATUS_RE = "RE"
STATUS_CE = "CE"
STATUS_SE = "SE"


@dataclass
class CaseResult:
    index: int
    status: str
    time_ms: int
    input_data: str = ""
    expected: str = ""
    actual: str = ""
    message: str = ""


@dataclass
class JudgeResult:
    status: str
    message: str = ""
    passed: int = 0
    total: int = 0
    time_ms: int = 0
    cases: list[CaseResult] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return self.status == STATUS_AC

    def to_dict(self) -> dict:
        return {
            "status": self.status,
            "message": self.message,
            "passed": self.passed,
            "total": self.total,
            "time_ms": self.time_ms,
            "cases": [c.__dict__ for c in self.cases],
        }


def normalize_output(text: str) -> str:
    """逐行去掉行尾空白、忽略末尾多余空行，避免"多一个空格/换行"被误判。"""
    if text is None:
        return ""
    lines = [line.rstrip() for line in text.replace("\r\n", "\n").replace("\r", "\n").split("\n")]
    while lines and not lines[-1]:
        lines.pop()
    return "\n".join(lines)


def _short(text: str, limit: int = 2000) -> str:
    if text is None:
        return ""
    if len(text) <= limit:
        return text
    return text[:limit] + f"\n…（输出过长，仅显示前 {limit} 个字符）"


def check_code(code: str) -> str | None:
    """编译期检查：语法错误 + 禁用模块。返回错误说明，None 表示通过。"""
    try:
        tree = ast.parse(code, filename="main.py")
    except SyntaxError as exc:
        line = exc.lineno or 0
        text = (exc.text or "").strip()
        tip = ERROR_TIPS.get("SyntaxError")
        where = f"第 {line} 行" + (f"（`{text}`）" if text else "")
        return f"{where}附近有语法错误：{exc.msg}\n提示：{tip}"
    except (ValueError, MemoryError) as exc:  # 罕见的编码/超长问题
        return f"代码无法解析：{exc}"

    for node in ast.walk(tree):
        names = []
        if isinstance(node, ast.Import):
            names = [alias.name.split(".")[0] for alias in node.names]
        elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
            names = [node.module.split(".")[0]]
        for name in names:
            if name in FORBIDDEN_MODULES:
                return (
                    f"代码第 {getattr(node, 'lineno', 0)} 行使用了评测环境禁止的模块：`{name}`。\n"
                    "提示：本系统只允许 Python 标准库中与算法无关的模块，请使用题目要求的方式解题。"
                )
    return None


def _friendly_error(stderr: str) -> str:
    """从 traceback 中提取最后一段异常和用户代码行号，翻译成中文提示。"""
    text = (stderr or "").strip()
    if not text:
        return "程序异常退出，但没有错误信息。"
    if "输出内容过多，已截断" in text:
        return "程序输出内容过多（超过 256KB），通常意味着多余打印或者死循环。"

    lines = [ln for ln in text.splitlines() if ln.strip()]
    exc_line = ""
    for ln in reversed(lines):
        stripped = ln.strip()
        if stripped.startswith("File "):
            break
        if ":" in stripped or stripped.endswith("Error") or stripped.endswith("Exception"):
            exc_line = stripped
            break

    exc_type = ""
    exc_msg = ""
    if exc_line:
        if ":" in exc_line:
            exc_type, _, exc_msg = exc_line.partition(":")
            exc_type = exc_type.strip()
            exc_msg = exc_msg.strip()
        else:
            exc_type = exc_line.strip()

    line_no = None
    for ln in lines:
        if "main.py" in ln and "line" in ln:
            try:
                line_no = int(ln.split("line")[1].split(",")[0].strip())
            except (IndexError, ValueError):
                line_no = None

    tip = ERROR_TIPS.get(exc_type)
    body = []
    if line_no:
        body.append(f"第 {line_no} 行")
    if exc_type:
        body.append(f"{exc_type}：{exc_msg}" if exc_msg and exc_msg != exc_type else exc_type)
    if not body:
        body.append("程序异常退出")
    message = "，".join(body)
    if tip:
        message += f"\n提示：{tip}"
    return message


def _run_case(code_path: str, input_data: str, timeout_ms: int, max_output: int) -> tuple:
    """执行一个测试点，返回 (status, time_ms, stdout, stderr)。"""
    env = {
        "PYTHONIOENCODING": "utf-8",
        "PYTHONUTF8": "1",
        "SYSTEMROOT": os.environ.get("SYSTEMROOT", ""),
        "PATH": os.environ.get("PATH", ""),
        "TEMP": os.environ.get("TEMP", ""),
        "TMP": os.environ.get("TMP", ""),
    }
    creationflags = 0x08000000 if os.name == "nt" else 0  # CREATE_NO_WINDOW
    started = time.perf_counter()
    try:
        proc = subprocess.run(
            [sys.executable, "-I", RUNNER, str(max_output), code_path],
            input=input_data.encode("utf-8"),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=os.path.dirname(code_path),
            env=env,
            timeout=timeout_ms / 1000.0,
            creationflags=creationflags,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        elapsed = int((time.perf_counter() - started) * 1000)
        out = exc.stdout or b""
        err = exc.stderr or b""
        return STATUS_TLE, elapsed, out.decode("utf-8", "replace"), err.decode("utf-8", "replace")

    elapsed = int((time.perf_counter() - started) * 1000)
    out = proc.stdout.decode("utf-8", "replace")
    err = proc.stderr.decode("utf-8", "replace")
    if proc.returncode != 0:
        return STATUS_RE, elapsed, out, err
    return STATUS_AC, elapsed, out, err


def judge(code: str, tests: list, time_limit_ms: int = 2000, max_output: int = 256 * 1024) -> JudgeResult:
    """对一段代码跑完全部测试点。tests 为 [{"input": str, "output": str}, ...]。"""
    code = code or ""
    if not code.strip():
        return JudgeResult(STATUS_CE, "代码为空，请先写代码再提交。", 0, len(tests))

    static_error = check_code(code)
    if static_error:
        return JudgeResult(STATUS_CE, static_error, 0, len(tests))

    if not tests:
        return JudgeResult(STATUS_SE, "题目缺少测试数据，请联系管理员补充。", 0, 0)

    cases: list[CaseResult] = []
    passed = 0
    max_time = 0
    verdict = STATUS_AC
    message = ""

    with tempfile.TemporaryDirectory(prefix="pyoj_") as tmpdir:
        code_path = os.path.join(tmpdir, "main.py")
        with open(code_path, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(code)

        for idx, case in enumerate(tests, start=1):
            input_data = case.get("input", "")
            expected_raw = case.get("output", "")
            status, elapsed, out, err = _run_case(code_path, input_data, time_limit_ms, max_output)
            max_time = max(max_time, elapsed)
            case_info = CaseResult(
                index=idx,
                status=status,
                time_ms=elapsed,
                input_data=input_data,
                expected=expected_raw,
                actual=out,
            )

            if status == STATUS_TLE:
                verdict = STATUS_TLE
                case_info.message = (
                    f"第 {idx} 个测试点运行超过 {time_limit_ms} ms 仍未结束。\n"
                    "提示：多半是死循环（while 条件永远为真），或者算法复杂度过高。"
                )
                message = case_info.message
                cases.append(case_info)
                break

            if status == STATUS_RE:
                verdict = STATUS_RE
                case_info.message = _friendly_error(err)
                message = case_info.message
                cases.append(case_info)
                break

            if normalize_output(out) != normalize_output(expected_raw):
                verdict = STATUS_WA
                case_info.message = f"第 {idx} 个测试点输出与标准答案不一致。"
                message = (
                    f"第 {idx} 个测试点答案错误。\n"
                    "建议：拿样例先自测一遍，注意输出格式（空格、换行、大小写）。"
                )
                cases.append(case_info)
                break

            case_info.status = STATUS_AC
            passed += 1
            cases.append(case_info)

    if verdict == STATUS_AC:
        message = f"恭喜！{len(tests)} 个测试点全部通过。"

    return JudgeResult(
        status=verdict,
        message=message,
        passed=passed,
        total=len(tests),
        time_ms=max_time,
        cases=cases,
    )
