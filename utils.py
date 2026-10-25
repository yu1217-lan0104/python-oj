"""通用小工具：题目富文本渲染、时间格式化、分页参数处理。"""

import html
import re

from markupsafe import Markup

_CODE_FENCE = re.compile(r"^```")
_INLINE_CODE = re.compile(r"`([^`]+)`")


def _inline(text: str) -> str:
    return _INLINE_CODE.sub(r"<code>\1</code>", text)


def render_rich(text: str) -> Markup:
    """把题库里的轻量文本渲染成 HTML。

    支持的写法只有两种：空行分段、``` 包裹的代码块，外加行内 `code`。
    先整体转义再做最小替换，因此题目内容里即使出现 HTML 也不会被执行。
    """
    if not text:
        return Markup("")

    lines = str(text).replace("\r\n", "\n").split("\n")
    blocks = []
    i = 0
    while i < len(lines):
        line = lines[i]
        if _CODE_FENCE.match(line.strip()):
            i += 1
            buf = []
            while i < len(lines) and not _CODE_FENCE.match(lines[i].strip()):
                buf.append(lines[i])
                i += 1
            i += 1
            blocks.append(
                '<pre class="problem-code">' + html.escape("\n".join(buf), quote=False) + "</pre>"
            )
        elif not line.strip():
            i += 1
        else:
            buf = []
            while i < len(lines) and lines[i].strip() and not _CODE_FENCE.match(lines[i].strip()):
                buf.append(lines[i])
                i += 1
            body = "<br>".join(_inline(html.escape(x, quote=False)) for x in buf)
            blocks.append(f"<p>{body}</p>")
    return Markup("\n".join(blocks))


def time_ago(dt) -> str:
    from datetime import datetime

    if not dt:
        return ""
    delta = datetime.now() - dt
    seconds = int(delta.total_seconds())
    if seconds < 60:
        return "刚刚"
    if seconds < 3600:
        return f"{seconds // 60} 分钟前"
    if seconds < 86400:
        return f"{seconds // 3600} 小时前"
    if seconds < 86400 * 7:
        return f"{seconds // 86400} 天前"
    return dt.strftime("%Y-%m-%d")


def fmt_dt(dt) -> str:
    return dt.strftime("%Y-%m-%d %H:%M:%S") if dt else ""


def clamp_int(value, default: int, low: int, high: int) -> int:
    try:
        num = int(value)
    except (TypeError, ValueError):
        return default
    return max(low, min(high, num))
