from flask import Blueprint, jsonify, render_template, request

from yacut import db

from http import HTTPStatus

bp_errors = Blueprint('errors', __name__)


def is_api_request():
    """Запрос пришёл к API (/api/...)."""
    return request.path.startswith('/api/')


@bp_errors.app_errorhandler(HTTPStatus.NOT_FOUND)
def page_not_found(error):
    if is_api_request():
        return jsonify(error='Not Found'), HTTPStatus.NOT_FOUND
    return render_template('404.html'), HTTPStatus.NOT_FOUND


@bp_errors.app_errorhandler(500)
def internal_error(error):
    db.session.rollback()
    if is_api_request():
        code = HTTPStatus.INTERNAL_SERVER_ERROR
        return jsonify(error='Internal Server Error'), code
    return render_template('500.html'), HTTPStatus.INTERNAL_SERVER_ERROR


class InvalidAPIUsage(Exception):
    """Кастомное исключение для API — бросаем в api_views.py."""
    status_code = HTTPStatus.BAD_REQUEST   # дефолт

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