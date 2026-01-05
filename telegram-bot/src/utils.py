from datetime import datetime
from pathlib import Path

import openai
from markitdown import MarkItDown

from .settings import TIMEZONE, settings


def current_datetime() -> datetime:
    """Получение текущего времени в выбранном часовом поясе"""

    return datetime.now(TIMEZONE)


def convert_document_to_md(path: Path) -> str:
    '''client = openai.OpenAI(
        api_key=settings.yandexcloud.apikey,
        base_url=settings.yandexcloud.base_url,
        project=settings.yandexcloud.folder_id,
    )'''
    md = MarkItDown()
    result = md.convert(path)
    return result.text_content
