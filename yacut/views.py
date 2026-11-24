import aiohttp
from urllib.parse import unquote, quote

from http import HTTPStatus

from flask import (
    Blueprint,
    abort,
    flash,
    redirect,
    render_template,
    url_for,
    Response,
    abort
)

from yacut import db
from yacut.forms import FileUploadForm, URLForm
from yacut.models import URLMap
from yacut.yandex_disk import async_upload_files_to_yandex_disk

from yacut.constants import (
    RESERVED_IDS,
    YANDEX_DOWNLOAD_PREFIX
)

views = Blueprint('views', __name__)


# Регистрируем роуты
@views.route('/', methods=['GET', 'POST'])
def index_view():
    form = URLForm()
    short_link = None

    if form.validate_on_submit():
        custom_id = (form.custom_id.data or '').strip()
        original = form.original_link.data.strip()

        if custom_id:
            # Проверка на зарезервированный путь.
            if custom_id in RESERVED_IDS:
                flash('Предложенный вариант короткой ссылки уже существует.')
                return render_template('index.html', form=form)

            # Проверка на занятость.
            if URLMap.query.filter_by(short=custom_id).first() is not None:
                flash('Предложенный вариант короткой ссылки уже существует.')
                return render_template('index.html', form=form)

            short_id = custom_id
        else:
            short_id = URLMap.get_unique_short_id()

        url_map = URLMap(original=original, short=short_id)
        db.session.add(url_map)
        db.session.commit()

        # Составляем ссылку из "url_map"
        short_link = url_for(
            'views.redirect_view',
            short_id=short_id,
            _external=True
        )

    return render_template(
        'index.html',
        form=form,
        short_link=short_link,
    )


@views.route('/files', methods=['GET', 'POST'])
async def files():
    form = FileUploadForm()
    files_data = None

    if form.validate_on_submit():
        try:
            files_data = await async_upload_files_to_yandex_disk(
                form.files.data
            )
        except Exception as error:
            flash(f'Ошибка при загрузке файлов: {error}')
            return render_template('files.html', form=form, files=None)

        # Для каждого загруженного файла создаём короткую ссылку.
        result = []
        for item in files_data:
            short_id = URLMap.get_unique_short_id()
            url_map = URLMap(original=item['link'], short=short_id)
            db.session.add(url_map)
            db.session.commit()

            short_link = url_for(
                'views.redirect_view',
                short_id=short_id,
                _external=True,
            )
            result.append({
                'filename': item['filename'],
                'short_link': short_link,
            })
        files_data = result

    return render_template('files.html', form=form, files=files_data)


@views.route('/<short_id>')
async def redirect_view(short_id):
    url_map = URLMap.query.filter_by(short=short_id).first()
    if url_map is None:
        abort(HTTPStatus.NOT_FOUND)

    # Если это НЕ файл с Яндекса — обычный редирект
    if not url_map.original.startswith(YANDEX_DOWNLOAD_PREFIX):
        return redirect(url_map.original)

    async with aiohttp.ClientSession() as session:
        async with session.get(url_map.original) as resp:
            if resp.status != HTTPStatus.OK:
                abort(HTTPStatus.NOT_FOUND)
            file_data = await resp.read()
            content_disposition = resp.headers.get('Content-Disposition', '')

    # Достаём имя файла из Content-Disposition
    filename = 'file'
    if "filename*=UTF-8''" in content_disposition:
        raw = content_disposition.split("filename*=UTF-8''")[1]
        filename = unquote(raw.strip('"\''))
    elif 'filename=' in content_disposition:
        raw = content_disposition.split('filename=')[1]
        filename = unquote(raw.strip('"\''))

    # Кодируем для безопасной передачи в заголовке
    safe_filename = quote(filename)

    return Response(
        file_data,
        mimetype='application/octet-stream',
        headers={
            'Content-Disposition':
                f"attachment; filename*=UTF-8''{safe_filename}"  # noqa: E702
        }
    )
