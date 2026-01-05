from typing import Annotated, Literal, TypedDict

import logging
import operator
from pathlib import Path
from uuid import UUID

from langchain.messages import AIMessage, AnyMessage, SystemMessage, ToolMessage
from langchain_core.output_parsers import PydanticOutputParser, StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableSerializable
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.types import Command
from pydantic import BaseModel, Field

from ..core import schemas
from ..database import crud, models
from ..settings import PROMPTS_DIR, settings
from ..utils import convert_document_to_md

logger = logging.getLogger(__name__)

llm = ChatOpenAI(
    api_key=settings.yandexcloud.apikey,
    model=settings.yandexcloud.aliceai_llm,
    base_url=settings.yandexcloud.base_url,
    temperature=0.5,
    max_retries=3
)

SYSTEM_PROMPT = (PROMPTS_DIR / "course_structure_designer.md").read_text(encoding="utf-8")


@tool
async def get_materials_metadata(attachment_ids: list[UUID]) -> list[str]:
    """Получает метаданные прикреплённых материалов (полезно для первичного анализа).

    Attributes:
        attachment_ids: Массив идентификаторов прикреплённых файлов.
    Returns:
        Список метаданных в формате JSON (размер файла, его mime-type, имя файла, ...)
    """

    attachments: list[str] = []
    for attachment_id in attachment_ids:
        attachment = await crud.read(
            attachment_id, model_class=models.Attachment, schema_class=schemas.Attachment
        )
        if attachment is None:
            continue
        attachments.append(attachment.model_dump_json(exclude={"filepath"}))
    return attachments


@tool
async def read_attached_material(attachment_id: UUID) -> str:
    """Читает прикреплённый материал.

    Attributes:
        attachment_id: Идентификатор прикреплённого файла.
    Returns:
        Контент содержимого файла в формате Markdown.
    """

    attachment = await crud.read(
        attachment_id, model_class=models.Attachment, schema_class=schemas.Attachment
    )
    if attachment is None:
        return "Файл не найден"
    md_text = convert_document_to_md(Path(attachment.filepath))
    return f"""**{attachment.original_filename}:**
    {md_text}
    """


async def criticize(
        teacher_prompt: str, proposed_course: str, old_critique: str | None = None
) -> str:
    """Получить справедливую критику по составленному курсу.

    Attributes:
        teacher_prompt: Исходный запрос преподавателя.
        proposed_course: Предложенная структура курса.
        old_critique: Последняя критика если есть (от предыдущего обращения)
    Returns:
        Обоснованная критика с предложениями по улучшению.
    """

    prompt = (PROMPTS_DIR / "course_structure_critic.md").read_text(encoding="utf-8")
    llm = ChatOpenAI(
        api_key=settings.yandexcloud.apikey,
        model=settings.yandexcloud.aliceai_llm,
        base_url=settings.yandexcloud.base_url,
        temperature=0.5,
    )
    chain = ChatPromptTemplate.from_template(prompt) | llm | StrOutputParser()
    return await chain.ainvoke({
        "teacher_prompt": teacher_prompt,
        "proposed_course": proposed_course,
        "old_critique": old_critique
    })


tools = [get_materials_metadata, read_attached_material]
llm_with_tools = llm.bind_tools(tools)
tools_by_names = {tool.name: tool for tool in tools}


class MessagesState(TypedDict):
    teacher_prompt: str
    messages: Annotated[list[AnyMessage], operator.add]
    critique: list[str]
    llm_calls: int


async def call_llm(state: MessagesState) -> dict[str, list[AnyMessage] | int]:
    logger.info("Calling LLM")
    message = await llm_with_tools.ainvoke(
                [SystemMessage(content=SYSTEM_PROMPT)] + state["messages"]
            )
    print(message)
    return {
        "messages": [
            message
        ],
        "llm_calls": state.get("llm_calls", 0) + 1
    }


async def tool_node(state: MessagesState) -> dict[str, list[ToolMessage]]:
    messages: list[ToolMessage] = []
    for tool_call in state["messages"][-1].tool_calls:
        tool = tools_by_names[tool_call["name"]]
        logger.info("Perform tool `%s` calling", tool_call["name"])
        result = await tool.ainvoke(tool_call["args"])
        messages.append(ToolMessage(content=result, tool_call_id=tool_call["id"]))
    return {"messages": messages}


async def critic_node(state: MessagesState) -> Command[Literal["call_llm", END]]:
    logger.info("Call critic node")

    prompt = (PROMPTS_DIR / "course_structure_critic.md").read_text(encoding="utf-8")

    class CriticOutput(BaseModel):
        action: Literal["accept", "reject", "improve"] = Field(
            ..., description="Действие которое нужно выполнить"
        )
        critique: list[str] = Field(
            default_factory=list,
            description="Добавь свои замечания если курс нужно улучшить или оставь пустым"
        )

    parser = PydanticOutputParser(pydantic_object=CriticOutput)
    chain: RunnableSerializable[dict[str, str], CriticOutput] = (
        ChatPromptTemplate.from_messages(
            [("system", prompt)]
        ).partial(format_instructions=parser.get_format_instructions())
        | llm
        | parser
    )
    response = await chain.ainvoke({
        "teacher_prompt": state["teacher_prompt"],
        "proposed_course": state["messages"][-1].content,
        "old_critique": "\n".join(state.get("critique", [])),
    })
    print(response)
    if response.action == "accept":
        logger.info("Accept course structure")
        return Command(update=state, goto=END)
    logger.info("%s course structure", response.action.title())
    return Command(
        update={
            "critique": response.critique,
            "messages": [AIMessage(content="\n".join(response.critique))],
        },
        goto="call_llm"
    )


def should_continue(state: MessagesState) -> Literal["tool_node", "critic_node"]:
    messages = state["messages"]
    last_message = messages[-1]
    if last_message.tool_calls:
        return "tool_node"
    return "critic_node"


checkpointer = InMemorySaver()

builder = StateGraph(MessagesState)

builder.add_node("call_llm", call_llm)
builder.add_node("tool_node", tool_node)
builder.add_node("critic_node", critic_node)

builder.add_edge(START, "call_llm")
builder.add_conditional_edges(
    "call_llm",
    should_continue,
    ["tool_node", "critic_node"]
)
builder.add_edge("tool_node", "call_llm")

agent = builder.compile(checkpointer=checkpointer)
