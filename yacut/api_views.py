from flask import Blueprint, jsonify, request

from http import HTTPStatus

from yacut import db
from yacut.error_handlers import InvalidAPIUsage
from yacut.models import URLMap
from yacut.constants import SHORT_API_ID_RE, RESERVED_IDS


api_bp = Blueprint('api', __name__, url_prefix='/api')


def is_valid_custom_id(custom_id):
    """Валидация кастомного id для API: 1-16 символов, латиница/цифры."""
    if not SHORT_API_ID_RE.fullmatch(custom_id):
        return False
    return custom_id not in RESERVED_IDS


@api_bp.route('/id/', methods=['POST'])
def create_short_link():
    # Проверяем, что тело вообще есть (до парсинга!)
    if not request.data:
        raise InvalidAPIUsage('Отсутствует тело запроса')

    #  Проверяем, что это JSON
    if not request.is_json:
        raise InvalidAPIUsage('Отсутствует тело запроса')

    # Парсим (silent=True — не выбрасывает исключение на битом JSON)
    data = request.get_json(silent=True)
    if not data:
        raise InvalidAPIUsage('Отсутствует тело запроса')

    url = data.get('url')
    if not url:
        raise InvalidAPIUsage('"url" является обязательным полем!')

    custom_id = data.get('custom_id')

    if custom_id:
        if not is_valid_custom_id(custom_id):
            raise InvalidAPIUsage(
                'Указано недопустимое имя для короткой ссылки'
            )
        if URLMap.get_by_short_id(custom_id) is not None:
            raise InvalidAPIUsage(
                'Предложенный вариант короткой ссылки уже существует.'
            )
        short_id = custom_id
    else:
        short_id = URLMap.get_unique_short_id()

    # Только формирую для записи в базу url
    url_map = URLMap(original=url, short=short_id)
    db.session.add(url_map)
    db.session.commit()

    # Забираю из модели с двуми полями
    return jsonify(url_map.to_dict_with_short_link()), HTTPStatus.CREATED


@api_bp.route('/id/<string:short_id>/', methods=['GET'])
def get_original_link(short_id):

    url_map = URLMap.get_by_short_id(short_id)

    if url_map is None:
        raise InvalidAPIUsage('Указанный id не найден', HTTPStatus.NOT_FOUND)
    return jsonify(url_map.to_dict()), HTTPStatus.OK