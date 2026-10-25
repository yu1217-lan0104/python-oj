@echo off
chcp 65001 >nul
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    echo [错误] 没有找到虚拟环境，请先按 README 的「快速开始」安装依赖。
    pause
    exit /b 1
)

echo 正在启动 Python 算法练习场：http://127.0.0.1:5000
.venv\Scripts\python.exe app.py
pause
