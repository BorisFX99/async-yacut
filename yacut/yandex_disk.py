import os
import asyncio
from urllib.parse import unquote

import aiohttp


API_HOST = 'https://cloud-api.yandex.net/'
API_VERSION = 'v1'
REQUEST_UPLOAD_URL = f'{API_HOST}{API_VERSION}/disk/resources/upload'
DOWNLOAD_LINK_URL = f'{API_HOST}{API_VERSION}/disk/resources/download'

DISK_TOKEN = os.getenv('DISK_TOKEN', '')
AUTH_HEADERS = {'Authorization': f'OAuth {DISK_TOKEN}'}


async def upload_file_to_disk(session, file):
    """
    Загружает ОДИН файл на Яндекс.Диск.
    :params
        session: Передаем одну сессию
        file: FileStorage из Flask (Werkzeug), у которого есть .filename и .read()
    :return: путь к файлу на Диске (str), например 'app:/filename.txt'
    """
    filename = file.filename
    path = f'app:/{filename}'

    async with session.get(
        REQUEST_UPLOAD_URL,
        headers=AUTH_HEADERS,
        params={'path': path, 'overwrite': 'True'},
    ) as resp:
        resp.raise_for_status()
        upload_url = (await resp.json())['href']

    # Загружаем файл по этому URL
    file.seek(0)  # На случай повторного чтения.
    file_data = file.read()  # bytes берем из FileStorage Flask
    async with session.put(upload_url, data=file_data) as resp:
        resp.raise_for_status()
        location = resp.headers['Location']

    # Декодируем %20 и убираем /disk в начале
    location = unquote(location).replace('/disk', '')
    return location


async def get_download_link(session, path):
    """
    Получает прямую ссылку на скачивание файла с Диска.
    :params
        session: Передаем одну сессию
        path: путь на Диске, например 'app:/filename.txt'
              или '/Приложения/Uploader/filename.txt'
    :return: str — ссылка вида https://downloader.disk.yandex.ru/...
    """

    async with session.get(
        DOWNLOAD_LINK_URL,
        headers=AUTH_HEADERS,
        params={'path': path},
    ) as resp:
        resp.raise_for_status()
        data = await resp.json()
        return data['href']


async def process_one_file(session, file, semaphore):
    """
    Загружает один файл и получает на него ссылку на скачивание.

    :params
        session: Общая ``aiohttp.ClientSession``.
        file: Файл из Flask-формы (``FileStorage``).
        param semaphore: Семафор, ограничивающий число одновременных загрузок.
    :return: Словарь ``{'filename': str, 'link': str}`` или ``None``,
        если файл пустой (без имени).
    """
    if not file or not file.filename:
        return None
    async with semaphore:
        path_on_disk = await upload_file_to_disk(session, file)
        link = await get_download_link(session, path_on_disk)
        return {'filename': file.filename, 'link': link}


async def async_upload_files_to_yandex_disk(files, max_concurrent=5):
    """
    Асинхронно загружает несколько файлов на Яндекс.Диск и получает
    для каждого прямую ссылку на скачивание.

    Файлы загружаются параллельно, но не более ``max_concurrent``.

    :params
        files: Список файлов из Flask-формы
            (``werkzeug.datastructures.FileStorage``).
        max_concurrent: Максимальное число одновременных загрузок.

    :return: Список словарей ``{'filename': str, 'link': str}`` для
        успешно загруженных файлов. Порядок может отличаться от входного,
        так как задачи выполняются параллельно.
    """
    semaphore = asyncio.Semaphore(max_concurrent)

    # Создаем одну сессию на веь пул
    async with aiohttp.ClientSession() as session:
        tasks = [
            process_one_file(session, f, semaphore)
            for f in files
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)

    return [
        r for r in results
        if r is not None and not isinstance(r, Exception)
    ]