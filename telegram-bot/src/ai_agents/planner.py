import logging
from uuid import UUID

from langchain.agents import AgentState, create_agent
from langchain.agents.middleware import ModelRequest, dynamic_prompt
from langchain.tools import ToolRuntime, tool
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import InMemorySaver
from pydantic import BaseModel

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


class PlannerState(AgentState):
    ...


@tool(parse_docstring=True)
async def attached_materials_search(
        runtime: ToolRuntime[PlannerContext, PlannerState], query: str
) -> list[str]:
    """Выполняет поиск по прикреплённым материалам к курсу по запросу"""

    return await search_materials(course_id=runtime.context.course_id, query=query)


@tool(parse_docstring=True)
def finalize() -> ...: ...


@dynamic_prompt
def system_prompt_with_teacher_inputs(request: ModelRequest) -> str:
    prompt = (PROMPTS_DIR / "planner.md").read_text(encoding="utf-8")
    teacher_inputs = request.runtime.context.get("teacher_inputs")
    return prompt.format(teacher_prompt=teacher_inputs.to_prompt())


agent = create_agent(
    model=model,
    tools=[attached_materials_search],
    middleware=[system_prompt_with_teacher_inputs],
    state_schema=PlannerState,
    context_schema=PlannerContext,
    checkpointer=InMemorySaver(),
)
