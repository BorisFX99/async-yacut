from flask_wtf import FlaskForm
from flask_wtf.file import FileRequired, MultipleFileField
from wtforms import StringField, SubmitField, URLField
from wtforms.validators import DataRequired, Length, Optional, Regexp


class URLForm(FlaskForm):
    original_link = URLField(
        'Длинная ссылка',
        validators=[
            DataRequired(message='Обязательное поле'),
            Length(1, 128)
        ],
    )
    custom_id = StringField(
        'Ваш вариант короткой ссылки',
        validators=[
            Optional(),
            Length(max=16, message='Короткая ссылка не должна превышать 16 символов'),
            Regexp(
                r'^[a-zA-Z0-9]+$',
                message='Короткая ссылка может содержать только латинские буквы и цифры',
            ),
        ],
    )
    submit = SubmitField('Создать')


class FileUploadForm(FlaskForm):
    files = MultipleFileField(
        'Выберите файлы',
        validators=[
            FileRequired(message='Выберите хотя бы один файл'),
        ],
    )
    submit = SubmitField('Загрузить')