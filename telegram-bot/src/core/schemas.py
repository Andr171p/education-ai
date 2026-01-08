from __future__ import annotations

from typing import Any

from datetime import datetime
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, NonNegativeInt, PositiveInt

from ..utils import current_datetime
from .enums import AssessmentType, BlockType, DifficultyLevel, TaskStatus, UserRole


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


class Task(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID = Field(default_factory=uuid4)
    created_at: datetime = Field(default_factory=current_datetime)
    updated_at: datetime = Field(default_factory=current_datetime)
    finished_at: datetime | None = None
    status: TaskStatus
    resource_id: UUID


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
    id: UUID = Field(default_factory=uuid4, description="Не указывать, генерируется автоматически")
    title: str = Field(..., description="Название модуля")
    description: str = Field(
        ..., description="Краткий обзор тем и технологий с которыми ознакомится студент"
    )
    order: NonNegativeInt = Field(..., description="Порядковый номер модуля")
    content_blocks: list[ContentBlock] = Field(
        default_factory=list,
        description="Вместо жесткой структуры — LEGO-подобные блоки"
    )
    assessments: list[Assessment] = Field(
        default_factory=list, description="Ассессменты для проверки знаний"
    )


class ContentBlock(BaseModel):
    """Универсальные блоки с контентом (LEGO-подобные блоки).

    Примеры data для разных типов:
     - type="text": {"content": "Markdown текст", "generated_by_ai": true}
     - type="video": {"url": "youtube.com/...", "platform": "youtube"}
     - type="interactive": {"widget_type": "quiz", "questions": [...]}
     - type="code_example": {"language": "python", "code": "print('hello')", "explanation": "..."}
     - type="reading": {"title": "Книга", "pages": "10-25", "link": "..."}
    """

    id: UUID = Field(default_factory=uuid4, description="Не указывать, генерируется автоматически")
    block_type: BlockType | str = Field(
        ..., description="Тип контент блока (строго из доступных enum)"
    )
    data: dict[str, Any] = Field(
        default_factory=dict,
        description="""Примеры data для разных типов:
        - block_type="text": {"content": "Markdown текст", "generated_by_ai": true}
        - block_type="video": {"url": "youtube.com/...", "platform": "youtube"}
        - block_type="interactive": {"widget_type": "quiz", "questions": [...]}
        - block_type="code_example": {"language": "python", "code": "print('hello')", "explanation": "..."}
        - block_type="reading": {"title": "Книга", "pages": "10-25", "link": "..."}
        """  # noqa: E501
    )


class Assessment(BaseModel):
    id: UUID = Field(default_factory=uuid4, description="Не указывать, генерируется автоматически")
    assessment_type: AssessmentType = Field(..., description="Тип ассессмента")
    title: str = Field(..., description="Название ассессмента")
    description: str = Field(..., description="Краткое описание (1-2 предложения)")
    verification_rules: dict[str, Any] = Field(
        default_factory=dict,
        description="Правила проверки и создания ассессмента",
        examples=[
            {"question_count": 10, "time_limit": 1800},  # Для теста
            {"programming_language": "C#", "repository_required": True},  # Для кода
            {"min_words": 500, "max_words": 1000},  # Для эссе
        ],
    )


class TeacherInputs(BaseModel):
    """Входные данные от преподавателя для создания курса"""

    user_id: PositiveInt
    discipline: str = Field(
        ...,
        description="Название дисциплины курса",
        examples=["Базы данных", "Информационная безопасность", "История России"],
    )
    target_audience: str = Field(
        ...,
        description="Для кого предназначен курс (образование, опыт, навыки)",
        examples=[
            "Студенты 2-3 курсов технических специальностей с базовым знанием Python",
            "Начинающие дизайнеры, знакомые с основами композиции",
            "Менеджеры проектов с опытом работы от 1 года",
        ]
    )
    difficulty_level: DifficultyLevel
    estimated_duration_hours: PositiveInt | None = Field(
        default=None, ge=1, le=200, description="Ориентировочное количество академических-часов"
    )
    attachments: list[UUID]
    external_links: list[HttpUrl] = Field(default_factory=list)
    comment: str | None = Field(
        default=None, description="Дополнительный комментарий от преподавателя"
    )

    def to_prompt(self) -> str:
        return f"""**Дисциплина курса:** `{self.discipline}`.
        **Целевая аудитория:** {self.target_audience}.
        **Уровень сложности:** {self.difficulty_level.value}.
        **Ориентировочная продолжительность курса:** {self.estimated_duration_hours} часов.
        **Внешние ссылки и ресурсы:** {
            "; ".join(str(external_link) for external_link in self.external_links)
        }.
        **Комментарий преподавателя:** {self.comment}
        """
