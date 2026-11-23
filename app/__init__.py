import secrets

from flask import Flask, abort, request, session

from app import database
from app.config import Config
from app.utils.errors import register_error_handlers
from app.services.menu_service import normalize
from app.utils.web import csrf_field, csrf_token, money, vi_label


def create_app(config_overrides=None):
    app = Flask(__name__)
    app.config.from_object(Config)
    if config_overrides:
        app.config.update(config_overrides)

    database.init_app(app)
    register_error_handlers(app)
    app.jinja_env.globals["csrf_token"] = csrf_token
    app.jinja_env.globals["csrf_field"] = csrf_field
    app.jinja_env.filters["money"] = money
    app.jinja_env.filters["vi"] = vi_label
    app.jinja_env.filters["norm"] = normalize

    @app.before_request
    def csrf_protect():
        # Chống CSRF: mọi form POST phải mang token trùng với token trong phiên
        if request.method == "POST" and app.config["CSRF_ENABLED"]:
            sent = request.form.get("_csrf", "")
            if not sent or not secrets.compare_digest(sent, session.get("_csrf", "")):
                abort(400)

    from app.controllers import (auth_controller, customer_controller, kitchen_controller,
                                 menu_controller, order_controller, payment_controller,
                                 table_controller)
    for module in (auth_controller, menu_controller, table_controller, order_controller,
                   customer_controller, kitchen_controller, payment_controller):
        app.register_blueprint(module.bp)

    with app.app_context():
        database.init_db()
    return app
