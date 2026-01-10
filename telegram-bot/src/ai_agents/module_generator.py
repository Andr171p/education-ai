from typing import Any, TypedDict

import logging

import aiohttp
from langchain.agents import create_agent
from langchain.agents.middleware import ModelRequest, SummarizationMiddleware, dynamic_prompt
from langchain_core.output_parsers import PydanticOutputParser, StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableSerializable
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI

from ..core import enums, schemas
from ..intergrations import yandex_search_api
from ..services import crawler
from ..settings import PROMPTS_DIR, settings
from .course_structure_planner import ModulePlan

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = (PROMPTS_DIR / "module_generator.md").read_text(encoding="utf-8")

llm = ChatOpenAI(
    api_key=settings.yandexcloud.apikey,
    model=settings.yandexcloud.qwen3_235b,
    base_url=settings.yandexcloud.base_url,
    temperature=0.2,
    max_retries=3,
    max_tokens=3000,
)


@tool(parse_docstring=True)
async def rutube_search(query: str) -> dict[str, Any]:
    """Выполняет поиск видео в RuTube.

    Args:
        query: Запрос для поиска видео.
    """

    logger.info("Call RuTube search tool with query: `%s`", query)
    async with aiohttp.ClientSession(base_url="https://rutube.ru/api/") as session, session.get(
        url="search/video", params={"query": query}
    ) as response:
        return await response.json()


@tool(parse_docstring=True)
async def web_search(query: str) -> list[dict[str, Any]]:
    """Выполняет поиск информации в интернете.

    Args:
        query: Поисковый запрос.
    """

    logger.info("Call Web search tool with query: `%s`", query)
    return await yandex_search_api.search_async(query)


@tool(parse_docstring=True)
async def browse_link(link: str) -> str:
    """Просматривает WEB-страницу по ссылке.

    Args:
        link: Ссылка на страницу.
    """

    return await crawler.crawl_web_page(link)


@tool(parse_docstring=True)
async def draw_mermaid_diagram(prompt: str) -> str:
    """Рисует Mermaid диаграмму по твоему подробному запросу.

    Args:
        prompt: Твоё ТЗ для генерации диаграммы.
    """

    model = ChatOpenAI(
        api_key=settings.yandexcloud.apikey,
        model=settings.yandexcloud.aliceai_llm,
        base_url=settings.yandexcloud.base_url,
        temperature=0.3,
        max_retries=3
    )
    system_prompt = (PROMPTS_DIR / "mermaid_artist.md").read_text(encoding="utf-8")
    chain = (
            ChatPromptTemplate.from_messages([("system", system_prompt)])
            | model
            | StrOutputParser()
    )
    return await chain.ainvoke({"messages": [("human", prompt)]})


@tool(parse_docstring=True)
async def write_code(language: str, prompt: str) -> str:
    """Инструмент для написания программного кода.

    Args:
        language: Язык программирования, на котором нужно написать код.
        prompt: Запрос для написания кода.
    """

    model = ChatOpenAI(
        api_key=settings.yandexcloud.apikey,
        model=settings.yandexcloud.qwen3_235b,
        base_url=settings.yandexcloud.base_url,
        temperature=0.2,
        max_tokens=3000,
        max_retries=3,
    )
    system_prompt = (PROMPTS_DIR / "code_writer.md").read_text(encoding="utf-8")
    chain = ChatPromptTemplate.from_template(system_prompt) | model | StrOutputParser()
    return await chain.ainvoke({"language": language, "prompt": prompt})


class ContentBlockContext(TypedDict):
    discipline: str
    module_title: str
    module_description: str
    module_order: int
    module_key_topics: list[str]
    module_learning_objectives: list[str]
    thoughts: str
    block_type: enums.BlockType
    block_plan: str


@dynamic_prompt
def content_block_generator_system_prompt(request: ModelRequest) -> str:
    system_prompt = (PROMPTS_DIR / "content_block_generator.md").read_text(encoding="utf-8")
    context = request.runtime.context
    return system_prompt.format(
        discipline=context.get("discipline"),
        title=context.get("module_title"),
        description=context.get("module_description"),
        order=context.get("module_order"),
        key_topics=", ".join(context.get("module_key_topics", [])),
        learning_objectives=", ".join(context.get("module_learning_objectives", [])),
        thoughts=context.get("thoughts"),
        block_type=context.get("block_type"),
        block_plan=context.get("block_plan"),
    )


content_block_generator_agent = create_agent(
    model=llm,
    tools=[web_search, browse_link, rutube_search, draw_mermaid_diagram],
    middleware=[
        content_block_generator_system_prompt,
        SummarizationMiddleware(
            model=llm, trigger=("tokens", 5000)
        )
    ],
    context_schema=ContentBlockContext,
    response_format=schemas.ContentBlock
)


async def generate_module(discipline: str, module_plan: ModulePlan) -> schemas.Module:
    logger.info("Generating %s module of discipline %s", module_plan.order, discipline)
    parser = PydanticOutputParser(pydantic_object=schemas.Module)
    prompt = ChatPromptTemplate.from_messages([
        ("system", SYSTEM_PROMPT),
    ]).partial(format_instructions=parser.get_format_instructions())
    chain: RunnableSerializable[dict[str, str], schemas.Module] = prompt | llm | parser
    return await chain.ainvoke({
        "discipline": discipline, "module_note": module_plan.model_dump_json(),
    })
