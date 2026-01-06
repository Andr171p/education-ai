from __future__ import annotations

import logging
from pathlib import Path
from uuid import UUID

from langchain_core.messages import HumanMessage
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableSerializable
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field, NonNegativeInt, PositiveInt

from ..core import schemas
from ..database import crud, models
from ..settings import PROMPTS_DIR, settings
from ..utils import convert_document_to_md

logger = logging.getLogger(__name__)

llm = ChatOpenAI(
    api_key=settings.yandexcloud.apikey,
    model=settings.yandexcloud.aliceai_llm,
    base_url=settings.yandexcloud.base_url,
    temperature=0,
    max_retries=3
)

SYSTEM_PROMPT = (PROMPTS_DIR / "course_structure_planner.md").read_text(encoding="utf-8")


async def load_attached_materials(attachment_ids: list[UUID]) -> list[HumanMessage]:
    logger.info("Start loading attached materials")
    messages: list[HumanMessage] = []
    for attachment_id in attachment_ids:
        attachment = await crud.read(
            attachment_id, model_class=models.Attachment, schema_class=schemas.Attachment
        )
        if attachment is None:
            logger.warning("Material %s is not attached, skip this", attachment_id)
            continue
        md_text = convert_document_to_md(Path(attachment.filepath))
        messages.append(HumanMessage(
            content=f"""**Attachment-ID:** {attachment_id}
            **Filename:** {attachment.original_filename}

            {md_text}
            """
        ))
        logger.info("`%s` file loaded in agent conversation memory", attachment.original_filename)
    logger.info("Successfully loaded %s attached materials", len(messages))
    return messages


class CourseStructurePlan(BaseModel):
    modules_count: PositiveInt = Field(
        ...,
        ge=3, le=12,
        description="""Оптимальное количество модулей
        (в зависимости от объема и сложности материала)"""
    )
    topics_to_study: set[str] = Field(
        ..., min_length=5, description="Обязательные темы для изучения (минимум 5)"
    )
    module_notes: list[ModuleNote] = Field(..., description="Твои заметки по каждому из модулей")


class ModuleNote(BaseModel):
    title: str = Field(..., description="Примерное название модуля")
    order: NonNegativeInt = Field(
        ..., description="Порядковый номер модуля (нумерация начинается с нуля)"
    )
    key_topics: set[str] = Field(
        ...,
        min_length=2, max_length=6,
        description="Ключевые темы модуля (2-6 штуки)"
    )
    learning_objectives: list[str] = Field(
        ...,
        min_length=2, max_length=6,
        description="Цели обучения для этого модуля"
    )
    academic_hours: PositiveInt = Field(
        ..., description="Примерное количество академических часов"
    )
    thoughts: str = Field(
        ...,
        description="""Опиши свой мысли и планы по поводу этого модуля, например:
        какие уровни таксономии Блума использовать, какие методы преподавания
        будут максимально эффективны, определи стратегии оценивания знаний будь это тесты или
        итоговый проект и.т.д, продумай сложность и когнитивную нагрузку, как и где использовать
        материалы преподавателя ...
        """
    )


async def plan_course_structure(teacher_inputs: schemas.TeacherInputs) -> CourseStructurePlan:
    attachments_messages = await load_attached_materials(teacher_inputs.attachments)
    parser = PydanticOutputParser(pydantic_object=CourseStructurePlan)
    prompt = ChatPromptTemplate.from_messages([
        ("system", SYSTEM_PROMPT),
        ("human", "{teacher_prompt}"),
        *attachments_messages,
        ("human", "Выведи только следующую информацию в формате JSON: {format_instructions}")
    ]).partial(format_instructions=parser.get_format_instructions())
    logger.info("Planning course structure for discipline %s", teacher_inputs.discipline)
    chain: RunnableSerializable[dict[str, str], CourseStructurePlan] = prompt | llm | parser
    return await chain.ainvoke({"teacher_prompt": teacher_inputs.to_prompt()})
