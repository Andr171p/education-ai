from __future__ import annotations

from typing import Any

from datetime import datetime
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, NonNegativeInt, PositiveInt

from ..utils import current_datetime
from .enums import AssessmentType, BlockType, UserRole


class User(BaseModel):
    id: PositiveInt
    username: str
    role: UserRole


class File(BaseModel):
    path: str
    size: PositiveInt
    mime_type: str
    data: bytes
    uploaded_at: datetime


class Attachment(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID = Field(default_factory=uuid4)
    original_filename: str
    filepath: str
    mime_type: str
    size: PositiveInt
    uploaded_at: datetime = Field(default_factory=current_datetime)


class Course(BaseModel):
    """Модель образовательного курса"""

    id: UUID = Field(default_factory=uuid4)
    created_at: datetime = Field(default_factory=current_datetime)
    title: str = Field(
        ...,
        description="Понятное название курса",
        examples=["Разработка веб-приложений на Python с использованием Django"]
    )
    description: str = Field(..., description="Общее описание и введение в курс")
    discipline: str = Field(
        ...,
        description="Название дисциплины",
        examples=["Базы данных", "Информационная безопасность", "История России"]
    )
    creator_id: PositiveInt = Field(..., description="Telegram ID пользователя")


class Module(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    title: str = Field(..., description="Название модуля")
    description: str = Field(
        ..., description="Краткий обзор тем и технологий с которыми ознакомится студент"
    )
    order: NonNegativeInt = Field(..., description="Порядковый номер модуля")
    content_blocks: list[ContentBlock] = Field(
        default_factory=list,
        description="Вместо жесткой структуры — LEGO-подобные блоки"
    )
    assessments: list[Assessment] = Field(default_factory=list)
    dependencies: list[UUID] = Field(default_factory=list)


class ContentBlock(BaseModel):
    """Универсальные блоки с контентом (LEGO-подобные блоки).

    Примеры data для разных типов:
     - type="text": {"content": "Markdown текст", "generated_by_ai": true}
     - type="video": {"url": "youtube.com/...", "platform": "youtube"}
     - type="interactive": {"widget_type": "quiz", "questions": [...]}
     - type="code_example": {"language": "python", "code": "print('hello')", "explanation": "..."}
     - type="reading": {"title": "Книга", "pages": "10-25", "link": "..."}
    """

    id: UUID = Field(default_factory=uuid4)
    block_type: BlockType
    data: dict[str, Any] = Field(default_factory=dict)


class Assessment(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    assessment_type: AssessmentType
    title: str
    description: str
    verification_rules: dict[str, Any] = Field(
        default_factory=dict,
        description="Правила проверки и создания ассессмента",
        examples=[
            {"question_count": 10, "time_limit": 1800},  # Для теста
            {"test_framework": "pytest", "repository_required": True},  # Для кода
            {"min_words": 500, "max_words": 1000},  # Для эссе
        ],
    )


class TeacherInputs(BaseModel):
    """Входные данные от преподавателя для создания курса"""

    user_id: PositiveInt
    discipline: str
    comment: str
    attachments: list[UUID]
    external_links: list[HttpUrl] = Field(default_factory=list)

    def to_prompt(self) -> str:
        return f"""**User-ID:** {self.user_id}

        На основе предоставленных материалов создай образовательный курс
        по дисциплине {self.discipline}.

        **Комментарий преподавателя:**
        {self.comment}

        **ID прикреплённых файлов:**
        {'; '.join([str(attachment) for attachment in self.attachments])}

        **Прикреплённые ссылки:**
        {'; '.join([str(external_link) for external_link in self.external_links])}

        Основные требования:
         1. Учитывай прикреплённые материалы:
            - Используй контент из загруженных файлов как основу
            - Интегрируй примеры и задания из материалов преподавателя
            - Сохраняй терминологию и подходы преподавателя
        2. Структура курса:
            - Определи логичную последовательность модулей
            - Сбалансируй теорию и практику
            - Включи проверочные задания после каждой темы
        3. Формат материалов:
            - Используй разнообразные форматы (текст, видео, интерактив)
            - Добавь реальные примеры и кейсы
            - Включи ссылки на дополнительные ресурсы при необходимости
        4. Адаптация:
            - Учитывайте комментарии преподавателя
            - Подберите соответствующий уровень сложности
            - Предложите дифференцированные задания для разного уровня подготовки

        ВАЖНО: Максимально используй материалы преподавателя, если их достаточно.
        """
