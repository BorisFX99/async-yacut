import re
import string

SHORT_API_ID_RE = re.compile(r'^[a-zA-Z0-9]{1,16}$')
RESERVED_IDS = {'files'}
SHORT_ID_LENGTH = 6
# Создаём набор допустимых символов из которых генерить ссылку короткую'
SHORT_ID_CHARS = string.ascii_letters + string.digits
# Максимальное число попыток генерации уникального id.
SHORT_ID_MAX_ATTEMPTS = 100

# SHORT_ID_RE = re.compile(r'^[a-zA-Z0-9]+$')
# Префикс прямых ссылок на скачивание с Яндекс.Диска
YANDEX_DOWNLOAD_PREFIX = 'https://downloader.disk.yandex.ru/'

# Валидация форм
FORM_ORIGINAL_LINK_MIN_LEN = 1
FORM_ORIGINAL_LINK_MAX_LEN = 128
FORM_CUSTOM_ID_REGEX = r'^[a-zA-Z0-9]+$'

# Длины полей моделей
ORIGINAL_LINK_MAX_LEN = 2048
SHORT_ID_MAX_LEN = 16