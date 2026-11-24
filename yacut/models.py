from datetime import datetime
from random import choices

from flask import url_for

from yacut import db

from yacut.constants import (
    SHORT_ID_LENGTH,
    SHORT_ID_CHARS,
    SHORT_ID_MAX_ATTEMPTS,
    ORIGINAL_LINK_MAX_LEN,
    SHORT_ID_MAX_LEN
)


class URLMap(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    original = db.Column(db.String(ORIGINAL_LINK_MAX_LEN), nullable=False)
    short = db.Column(db.String(SHORT_ID_MAX_LEN), unique=True, nullable=False)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)

    def to_dict_with_short_link(self):
        """Представление для создания: url + абсолютная короткая ссылка."""
        return dict(
            url=self.original,
            short_link=url_for(
                'views.redirect_view',
                short_id=self.short,
                _external=True,
            ),
        )

    def to_dict(self):
        """Базовое представление: только исходный URL."""
        return dict(url=self.original)

    def from_dict(self, data):
        for field in ['original', 'short']:
            if field in data:
                setattr(self, field, data[field])

    @classmethod
    def get_unique_short_id(cls):
        """Генерирует уникальный 6-символьный id: буквы + цифры.

        Делает не более SHORT_ID_MAX_ATTEMPTS попыток; если уникальный
        id получить не удалось — выбрасывает RuntimeError.
        """
        for _ in range(SHORT_ID_MAX_ATTEMPTS):
            short_id = ''.join(choices(SHORT_ID_CHARS, k=SHORT_ID_LENGTH))
            if cls.get_by_short_id(short=short_id) is None:
                return short_id
        raise RuntimeError(
            'Не удалось сгенерировать уникальный короткий id '
            f'за {SHORT_ID_MAX_ATTEMPTS} попыток'
        )

    @classmethod
    def get_by_short_id(cls, short):
        """Возвращает URLMap по короткому id или None."""
        return cls.query.filter_by(short=short).first()
