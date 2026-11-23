import asyncio
import traceback
from pathlib import Path

import aiohttp
from dotenv import load_dotenv

load_dotenv()

from yacut.yandex_disk import (
    AUTH_HEADERS,
    DOWNLOAD_LINK_URL,
    REQUEST_UPLOAD_URL,
    get_download_link,
    upload_file_to_disk,
)


class FakeFile:
    """Имитация FileStorage — чтобы не поднимать Flask-форму."""

    def __init__(self, path):
        self.filename = Path(path).name
        self._data = Path(path).read_bytes()
        print(f'[FakeFile] Создан: filename={self.filename!r}, '
              f'размер={len(self._data)} байт')

    def read(self):
        print(f'[FakeFile] read() → {len(self._data)} байт')
        return self._data

    def seek(self, pos):
        print(f'[FakeFile] seek({pos})')


async def main():
    file_path = 'requirements.txt'
    print(f'=== 1. Берём файл: {file_path}')
    fake = FakeFile(file_path)

    print('\n=== 2. Загружаем файл на Диск ===')
    print(f'[upload] URL запроса: {REQUEST_UPLOAD_URL}')
    print(f'[upload] Заголовки: {AUTH_HEADERS}')
    print(f'[upload] filename: {fake.filename!r}')

    async with aiohttp.ClientSession() as session:
        # Шаг 2.1: запрос URL для загрузки
        print('\n--- 2.1. Запрос URL для загрузки ---')
        async with session.get(
            REQUEST_UPLOAD_URL,
            headers=AUTH_HEADERS,
            params={'path': f'app:/{fake.filename}', 'overwrite': 'True'},
        ) as resp:
            print(f'[upload] Status: {resp.status}')
            print(f'[upload] Content-Type: {resp.headers.get("Content-Type")}')
            body = await resp.json()
            print(f'[upload] Ответ JSON: {body}')
            upload_url = body['href']
            print(f'[upload] upload_url: {upload_url[:100]}...')

        # Шаг 2.2: загрузка файла
        print('\n--- 2.2. Загрузка файла по upload_url ---')
        fake.seek(0)
        file_data = fake.read()
        async with session.put(upload_url, data=file_data) as resp:
            print(f'[upload] Status: {resp.status}')
            print(f'[upload] Заголовки ответа:')
            for key, value in resp.headers.items():
                print(f'    {key}: {value}')
            location = resp.headers.get('Location', '')
            print(f'[upload] Location (сырой): {location}')

    print('\n=== 3. Получаем путь на Диске ===')
    # Декодируем и убираем /disk
    from urllib.parse import unquote
    path_on_disk = unquote(location).replace('/disk', '')
    print(f'[path] Путь на Диске: {path_on_disk!r}')

    print('\n=== 4. Получаем ссылку на скачивание ===')
    print(f'[download] URL запроса: {DOWNLOAD_LINK_URL}')
    print(f'[download] path: {path_on_disk!r}')
    async with aiohttp.ClientSession() as session:
        async with session.get(
            DOWNLOAD_LINK_URL,
            headers=AUTH_HEADERS,
            params={'path': path_on_disk},
        ) as resp:
            print(f'[download] Status: {resp.status}')
            print(f'[download] Content-Type: {resp.headers.get("Content-Type")}')
            data = await resp.json()
            print(f'[download] Ответ JSON: {data}')
            link = data.get('href', '')
            print(f'[download] Ссылка на скачивание: {link[:120]}...')

    print('\n=== 5. ИТОГ ===')
    print(f'Файл: {fake.filename}')
    print(f'Путь на Диске: {path_on_disk}')
    print(f'Ссылка на скачивание: {link}')


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except Exception:
        traceback.print_exc()