"""配置模块。

数据库默认使用 MySQL（与策划书技术选型一致）；如果本机没有可用的 MySQL，
只需把 DATABASE_URL 改成 SQLite 即可零配置启动，业务代码完全不用改动：

    MySQL : mysql+pymysql://root:密码@127.0.0.1:3306/pyoj?charset=utf8mb4
    SQLite: sqlite:///pyoj.db

配置读取顺序：环境变量 > 项目根目录 .env 文件 > 代码默认值。
"""

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent


def _load_dotenv(path: Path) -> dict:
    """极简 .env 解析，避免为了几行配置额外引入依赖。"""
    values = {}
    if not path.exists():
        return values
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, val = line.partition("=")
        values[key.strip()] = val.strip().strip('"').strip("'")
    return values


DOTENV = _load_dotenv(BASE_DIR / ".env")


def env(key: str, default: str | None = None) -> str | None:
    return os.environ.get(key) or DOTENV.get(key) or default


DEFAULT_SQLITE = "sqlite:///" + (BASE_DIR / "pyoj.db").as_posix()


class Config:
    SECRET_KEY = env("SECRET_KEY", "dev-secret-change-me-in-production")
    SQLALCHEMY_DATABASE_URI = env("DATABASE_URL", DEFAULT_SQLITE)
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {"pool_pre_ping": True, "pool_recycle": 3600}

    # 评测相关
    JUDGE_TIME_LIMIT_MS = int(env("JUDGE_TIME_LIMIT_MS", "2000"))
    JUDGE_MAX_CODE_BYTES = 64 * 1024
    JUDGE_MAX_OUTPUT_BYTES = 256 * 1024

    HOST = env("HOST", "127.0.0.1")
    PORT = int(env("PORT", "5000"))
    DEBUG = env("FLASK_DEBUG", "1") == "1"


def is_sqlite(uri: str) -> bool:
    return uri.startswith("sqlite")


def database_name(uri: str) -> str:
    """给页面/日志展示用：不暴露密码。"""
    if is_sqlite(uri):
        return "SQLite（本地文件）"
    tail = uri.rsplit("/", 1)[-1]
    name = tail.split("?", 1)[0]
    backend = uri.split(":", 1)[0].split("+", 1)[0]
    return f"{backend} / {name}"
