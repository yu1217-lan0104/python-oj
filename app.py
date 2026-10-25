"""Flask 应用工厂：注册扩展、蓝图、模板过滤器与错误页。"""

import secrets

from flask import Flask, abort, render_template, request, session

import utils
from config import Config, database_name
from extensions import db, login_manager
from models import DIFFICULTIES, STATUS_COLOR, STATUS_TEXT


def create_app(config_object=Config) -> Flask:
    app = Flask(__name__)
    app.config.from_object(config_object)
    app.url_map.strict_slashes = False

    db.init_app(app)
    login_manager.init_app(app)

    from views.auth import bp as auth_bp
    from views.cards import bp as cards_bp
    from views.main import bp as main_bp
    from views.problems import bp as problems_bp
    from views.profile import bp as profile_bp
    from views.records import bp as records_bp
    from views.report import bp as report_bp
    from views.topics import bp as topics_bp

    for bp in (main_bp, auth_bp, problems_bp, topics_bp, cards_bp, records_bp, report_bp, profile_bp):
        app.register_blueprint(bp)

    app.jinja_env.filters["rich"] = utils.render_rich
    app.jinja_env.filters["ago"] = utils.time_ago
    app.jinja_env.filters["dt"] = utils.fmt_dt

    @app.context_processor
    def inject_globals():
        if "_csrf" not in session:
            session["_csrf"] = secrets.token_urlsafe(24)
        return {
            "csrf_token": session["_csrf"],
            "STATUS_TEXT": STATUS_TEXT,
            "STATUS_COLOR": STATUS_COLOR,
            "DIFFICULTIES": DIFFICULTIES,
            "db_label": database_name(app.config["SQLALCHEMY_DATABASE_URI"]),
        }

    @app.before_request
    def csrf_protect():
        if request.method in ("POST", "PUT", "DELETE"):
            token = session.get("_csrf")
            sent = request.form.get("_csrf") or request.headers.get("X-CSRF-Token")
            if not token or token != sent:
                abort(400, description="表单已过期，请返回上一页刷新后重试。")

    @app.errorhandler(400)
    def bad_request(err):
        return render_template("errors/error.html", code=400, title="请求无效",
                               detail=getattr(err, "description", "请求参数不正确。")), 400

    @app.errorhandler(404)
    def not_found(err):
        return render_template("errors/error.html", code=404, title="页面不存在",
                               detail="可能是题目编号不对，或者链接已经失效。"), 404

    @app.errorhandler(500)
    def server_error(err):  # pragma: no cover
        db.session.rollback()
        return render_template("errors/error.html", code=500, title="服务器开小差了",
                               detail="请查看控制台日志，修复后刷新页面重试。"), 500

    return app


app = create_app()


if __name__ == "__main__":
    app.run(host=app.config["HOST"], port=app.config["PORT"], debug=app.config["DEBUG"])
