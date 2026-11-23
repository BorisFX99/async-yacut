import re

from flask import Blueprint, jsonify, request, url_for

from yacut import db
from yacut.error_handlers import InvalidAPIUsage
from yacut.models import URLMap
from yacut.views import get_unique_short_id  # переиспользуем генератор

api_bp = Blueprint('api', __name__, url_prefix='/api')

SHORT_ID_RE = re.compile(r'^[a-zA-Z0-9]{1,16}$')
RESERVED_IDS = {'files'}


def is_valid_custom_id(custom_id):
    """Валидация кастомного id для API: 1-16 символов, латиница/цифры."""
    return bool(SHORT_ID_RE.match(custom_id)) and custom_id not in RESERVED_IDS


@api_bp.route('/id/', methods=['POST'])
def create_short_link():
    if not request.is_json:
        raise InvalidAPIUsage('Тело запроса должно быть json')

    data = request.get_json()
    if not data:
        raise InvalidAPIUsage('Отсутствует тело запроса')

    url = data.get('url')
    if not url:
        raise InvalidAPIUsage('"url" является обязательным полем!')

    custom_id = data.get('custom_id')

    if custom_id:
        if not is_valid_custom_id(custom_id):
            raise InvalidAPIUsage('Указано недопустимое имя для короткой ссылки')
        if URLMap.query.filter_by(short=custom_id).first() is not None:
            raise InvalidAPIUsage('Предложенный вариант короткой ссылки уже существует.')
        short_id = custom_id
    else:
        short_id = get_unique_short_id()

    url_map = URLMap(original=url, short=short_id)
    db.session.add(url_map)
    db.session.commit()

    return jsonify({
        'url': url_map.original,
        'short_link': url_for('views.redirect_view', short_id=url_map.short, _external=True),
    }), 201


@api_bp.route('/id/<string:short_id>/', methods=['GET'])
def get_original_link(short_id):
    url_map = URLMap.query.filter_by(short=short_id).first()
    if url_map is None:
        raise InvalidAPIUsage('Указанный id не найден', status_code=404)
    return jsonify(url_map.to_dict()), 200