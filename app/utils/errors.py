import logging

from flask import render_template

log = logging.getLogger("restaurant")


def register_error_handlers(app):
    @app.errorhandler(400)
    def bad_request(_e):
        return render_template("error.html", code=400,
                               message="Invalid request or your session has expired. Please reload the page."), 400

    @app.errorhandler(403)
    def forbidden(_e):
        return render_template("error.html", code=403,
                               message="You do not have permission to use this function."), 403

    @app.errorhandler(404)
    def not_found(_e):
        return render_template("error.html", code=404,
                               message="Page not found."), 404

    @app.errorhandler(500)
    def server_error(e):
        log.exception("Lỗi hệ thống: %s", e)
        return render_template("error.html", code=500,
                               message="A system error occurred. Please try again."), 500
