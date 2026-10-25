"""全局扩展对象，单独成文件以避免 app / models 之间的循环导入。"""

from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = "auth.login"
login_manager.login_message = "请先登录后再继续操作。"
login_manager.login_message_category = "warning"
