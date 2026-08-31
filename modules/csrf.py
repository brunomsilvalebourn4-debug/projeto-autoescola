import secrets
from hmac import compare_digest

from flask import abort, request, session


def csrf_token():
    if "csrf_token" not in session:
        session["csrf_token"] = secrets.token_urlsafe(32)
    return session["csrf_token"]


def init_app(app):
    app.jinja_env.globals["csrf_token"] = csrf_token

    @app.before_request
    def protect_csrf():
        if not app.config.get("CSRF_ENABLED", True):
            return None
        if request.method in {"POST", "PUT", "PATCH", "DELETE"}:
            expected = session.get("csrf_token", "")
            received = request.form.get("csrf_token", "") or request.headers.get("X-CSRF-Token", "")
            if not expected or not received or not compare_digest(expected, received):
                abort(400, description="Token de segurança inválido ou expirado.")
        return None
