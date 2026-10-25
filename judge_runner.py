"""评测子进程的入口脚本（由 judge.py 调用，不直接给用户执行）。

作用：限制程序的标准输出体积，避免 `while True: print(x)` 这类新手常见写法
把内存吃满；正常输出与 `input()` 的行为完全不受影响。

用法：python -I judge_runner.py <输出上限字节> <用户代码文件>
"""

import runpy
import sys
import traceback

LIMIT = int(sys.argv[1])
TARGET = sys.argv[2]

_buf: list[str] = []
_used = 0
_overflow = False


class _CappedStdout:
    def __init__(self, real, limit: int):
        self._real = real
        self._limit = limit

    def write(self, s):
        global _used, _overflow
        if not isinstance(s, str):
            s = str(s)
        room = self._limit - _used
        if room > 0:
            piece = s[:room]
            _buf.append(piece)
            _used += len(piece)
        if len(s) > max(room, 0):
            _overflow = True
        return len(s)

    def flush(self):
        return None

    def writelines(self, lines):
        for line in lines:
            self.write(line)

    def isatty(self):
        return False

    @property
    def encoding(self):
        return "utf-8"

    def fileno(self):
        raise OSError("stdout 已被评测器接管，不支持 fileno()")


_real_stdout = sys.stdout
sys.stdout = _CappedStdout(_real_stdout, LIMIT)
sys.argv = [TARGET]

exit_code = 0
try:
    runpy.run_path(TARGET, run_name="__main__")
except SystemExit as exc:
    exit_code = int(exc.code or 0)
except BaseException:
    exit_code = 1
    traceback.print_exc()
finally:
    sys.stdout = _real_stdout
    _real_stdout.write("".join(_buf))
    _real_stdout.flush()
    if _overflow:
        sys.stderr.write("\n[verdict] 输出内容过多，已截断\n")
        sys.stderr.flush()

sys.exit(exit_code)
