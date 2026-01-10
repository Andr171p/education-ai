import logging
from uuid import UUID

from langchain.agents import create_agent
from langchain.agents.middleware import ModelRequest, dynamic_prompt
from langchain.agents.structured_output import ToolStrategy
from langchain.tools import ToolRuntime, tool
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field, NonNegativeInt

from ..core import schemas
from ..rag.attached_materials import search_materials
from ..settings import PROMPTS_DIR, settings

logger = logging.getLogger(__name__)

model = ChatOpenAI(
    api_key=settings.yandexcloud.apikey,
    model=settings.yandexcloud.aliceai_llm,
    base_url=settings.yandexcloud.base_url,
    temperature=0.5,
    max_retries=3
)


class PlannerContext(BaseModel):
    user_id: int
    course_id: UUID
    teacher_inputs: schemas.TeacherInputs


class ModuleNote(BaseModel):
    title: str = Field(..., description="Название модуля")
    description: str = Field(
        ..., description="Краткий обзор тем и технологий с которыми ознакомится студент"
    )
    order: NonNegativeInt = Field(
        ..., description="Порядковый номер модуля (нумерация начинается с нуля)"
    )
    note: str = Field(
        ..., description="Твои мысли и заметки для дизайнера модуля (максимально подробно)"
    )


class CourseStructurePlan(BaseModel):
    description: str = Field(..., description="Общее описание и введение в курс")
    module_notes: list[ModuleNote] = Field(..., description="Заметки по каждому из модулей")


@tool(parse_docstring=True)
async def attached_materials_search(runtime: ToolRuntime, query: str) -> list[str]:
    """Выполняет поиск по прикреплённым материалам к курсу по запросу

    Args:
        query: Запрос для поиска
    """

    return await search_materials(course_id=runtime.context.course_id, query=query)


@dynamic_prompt
def inject_teacher_inputs_in_system_prompt(request: ModelRequest) -> str:
    prompt = (PROMPTS_DIR / "course_structure_planner.md").read_text(encoding="utf-8")
    teacher_inputs: schemas.TeacherInputs = request.runtime.context.teacher_inputs
    if teacher_inputs is None:
        raise ValueError("Teacher inputs missing in context!")
    return prompt.format(teacher_prompt=teacher_inputs.to_prompt())


agent = create_agent(
    model=model,
    tools=[attached_materials_search],
    middleware=[inject_teacher_inputs_in_system_prompt],
    context_schema=PlannerContext,
    response_format=ToolStrategy(CourseStructurePlan)
)
