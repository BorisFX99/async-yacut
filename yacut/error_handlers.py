from flask import Blueprint, jsonify, render_template, request

from yacut import db

bp_errors = Blueprint('errors', __name__)


def is_api_request():
    """Запрос пришёл к API (/api/...)."""
    return request.path.startswith('/api/')


@bp_errors.app_errorhandler(404)
def page_not_found(error):
    if is_api_request():
        return jsonify(error='Not Found'), 404
    return render_template('404.html'), 404


@bp_errors.app_errorhandler(500)
def internal_error(error):
    db.session.rollback()
    if is_api_request():
        return jsonify(error='Internal Server Error'), 500
    return render_template('500.html'), 500


class InvalidAPIUsage(Exception):
    """Кастомное исключение для API — бросаем в api_views.py."""
    status_code = 400   # дефолт

    def __init__(self, message, status_code=None):
        super().__init__(message)
        self.message = message
        if status_code is not None:
            self.status_code = status_code

    def to_dict(self):
        return dict(message=self.message)


@bp_errors.app_errorhandler(InvalidAPIUsage)
def invalid_api_usage(error):
    return jsonify(error.to_dict()), error.status_code