import logging

from langchain.agents import create_agent
from langchain.agents.middleware import ModelRequest, dynamic_prompt
from langchain.agents.structured_output import ToolStrategy
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field, NonNegativeInt, PositiveInt

from ..core import enums
from ..settings import PROMPTS_DIR, settings
from .course_structure_planner import ModuleNote

logger = logging.getLogger(__name__)

model = ChatOpenAI(
    api_key=settings.yandexcloud.apikey,
    model=settings.yandexcloud.aliceai_llm,
    base_url=settings.yandexcloud.base_url,
    temperature=0.5,
    max_retries=3
)


class ModuleContext(BaseModel):
    course_description: str
    module_note: ModuleNote


class SequenceStep(BaseModel):
    number: NonNegativeInt = Field(..., description="")
    step_type: str
    purpose: str = Field(..., description="")
    estimated_minutes: PositiveInt = Field(..., description="")


class ContentBlock(BaseModel):
    block_type: enums.BlockType = Field(..., description="")
    main_concept: str = Field(..., description="")
    key_points: list[str] = Field(..., description="")
    specification: str = Field(..., description="")


class AssessmentFramework(BaseModel):
    assessment_type: enums.AssessmentType = Field(..., description="")
    purpose: str = Field(..., description="")
    difficulty: str = Field(..., description="")
    specification: str = Field(..., description="")


class ModuleDesign(BaseModel):
    """Дизайн модуля курса"""

    learning_sequence: list[SequenceStep] = Field(
        ..., description=""
    )
    content_blueprint: list[ContentBlock] = Field(
        ..., description=""
    )
    assessment_frameworks: list[AssessmentFramework] = Field(
        ..., description=""
    )


@dynamic_prompt
def inject_module_note_in_system_prompt(request: ModelRequest) -> str:
    prompt = (PROMPTS_DIR / "module_designer.md").read_text(encoding="utf-8")
    course_description: str = request.runtime.context.course_description
    module_note: ModuleNote = request.runtime.context.module_note
    return ...


agent = create_agent(
    model=model,
    tools=[],
    context_schema=ModuleContext,
    middleware=[inject_module_note_in_system_prompt],
    response_format=ToolStrategy(ModuleDesign)
)
