from typing import Any, Literal, TypedDict

import logging

import aiohttp
from langchain.agents import create_agent
from langchain.agents.middleware import ModelRequest, dynamic_prompt
from langchain_core.output_parsers import PydanticOutputParser, StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableSerializable
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI

from ..core import schemas
from ..intergrations import yandex_search_api
from ..services import crawler
from ..settings import PROMPTS_DIR, settings
from .course_structure_planner import ModulePlan

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = (PROMPTS_DIR / "module_generator.md").read_text(encoding="utf-8")

llm = ChatOpenAI(
    api_key=settings.yandexcloud.apikey,
    model=settings.yandexcloud.aliceai_llm,
    base_url=settings.yandexcloud.base_url,
    temperature=0,
    max_retries=3
)


@tool
async def rutube_search(query: str) -> dict[str, Any]:
    """Выполняет поиск видео в RuTube.

    Attributes:
        query: Запрос для поиска видео.
    """

    async with aiohttp.ClientSession(base_url="https://rutube.ru/api") as session, session.get(
        url="/search/video", params={"query": query}
    ) as response:
        return await response.json()


@tool
async def web_search(query: str) -> list[dict[str, Any]]:
    """Выполняет поиск информации в интернете.

    Attributes:
        query: Поисковый запрос.
    """

    return await yandex_search_api.search_async(query)


@tool
async def browse_link(link: str) -> str:
    """Просматривает WEB-страницу по ссылке.

    Attributes:
        link: Ссылка на страницу.
    """

    return await crawler.crawl_web_page(link)


@tool
async def draw_mermaid_diagram(prompt: str) -> str:
    """Рисует Mermaid диаграмму по твоему подробному запросу.

    Attributes:
        prompt: Твоё ТЗ для генерации диаграммы.
    Returns:
        Код Mermaid диаграммы.
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


@tool
async def write_program_code(programming_language: str, prompt: str) -> str:
    """Инструмент для написания программного кода.

    Attributes:
        programming_language: Язык программирования, на котором нужно написать код.
        prompt: Запрос для написания кода.
    """

    model = ChatOpenAI(
        api_key=settings.yandexcloud.apikey,
        model=settings.yandexcloud.qwen3_235b,
        base_url=settings.yandexcloud.base_url,
        temperature=0.2,
        max_retries=3,
    )
    system_prompt = (PROMPTS_DIR / "program_code_writer.md").read_text(encoding="utf-8")
    chain = ChatPromptTemplate.from_template(system_prompt) | model | StrOutputParser()
    return await chain.ainvoke({"language": programming_language, "prompt": prompt})


class ModuleContext(TypedDict):
    discipline: str
    content_type: Literal["content_block", "assessment"]
    module_plan: ModulePlan


@dynamic_prompt
def context_system_prompt(request: ModelRequest) -> str:
    discipline = request.runtime.context.get("discipline")
    content_type = request.runtime.context.get("content_type")
    module_plan = request.runtime.context.get("module_plan")
    match content_type:
        case "content_block":
            ...
        case "assessment":
            ...
    return SYSTEM_PROMPT.format(
        discipline=discipline, module_note=module_plan.model_dump_json()
    )


agent = create_agent(
    model=llm,
    tools=[web_search, browse_link, rutube_search, draw_mermaid_diagram],
    middleware=[context_system_prompt],
    context_schema=ModuleContext,
    response_format=schemas.Module
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
