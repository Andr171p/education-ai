from datetime import datetime
from pathlib import Path

from markitdown import MarkItDown

from .settings import TIMEZONE


def current_datetime() -> datetime:
    """Получение текущего времени в выбранном часовом поясе"""

    return datetime.now(TIMEZONE)


def convert_document_to_md(path: Path) -> str:
    md = MarkItDown()
    result = md.convert(path)
    return result.text_content
