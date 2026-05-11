# Агент для проверки теоретических знаний

from langchain.agents import create_agent
from langchain.agents.structured_output import ProviderStrategy, ToolStrategy
from langchain_openai import ChatOpenAI

from src.core.entities.course import (
    AnyKnowledgeTest,
    DetailedAnswerTest,
    Module,
    MultipleChoiceTest,
    TestType,
)
from src.settings import settings
from src.utils.formatting import get_module_context

# model = ChatOpenAI(
#     api_key=settings.yandexcloud.api_key,
#     model=settings.yandexcloud.qwen3_235b,
#     base_url=settings.yandexcloud.base_url,
#     temperature=0.2,
#     max_retries=3
# )

model = ChatOpenAI(
    api_key=settings.deepseek.api_key,
    base_url=settings.deepseek.base_url,
    model=settings.deepseek.deepseek_chat,
    temperature=0.2,
)

config = {
    TestType.MULTIPLE_CHOICE:
        {
            "system_prompt": """\
            ### Ограничения на размер ответа
             - Максимальная длина текста одного вопроса не должна превышать 600 символов
             «Максимальная длина формулировки вопроса (без вариантов) — 600 символов.
             Формулируй вопросы чётко и без воды, избегай длинных вступлений».

            Ты - эксперт по созданию тестов для проверки знаний.
            На основе предоставленного теоретического материала модуля сгенерируй тест
            в формате multiple choice (выбор одного или нескольких правильных ответов).
            Тест должен содержать от 10 до 30 вопросов, в зависимости от объема материала.
            Вопросы должны охватывать ключевые понятия, определения, принципы и факты из текста.
            Для каждого вопроса укажи:
             - текст вопроса,
             - список вариантов ответа (от 3 до 5 вариантов),
             - индекс правильного варианта ответа (индексация с 0),
             - баллы за вопрос (по умолчанию 1, если не указано иное).
            """,
            "response_format": ToolStrategy(MultipleChoiceTest),
        },
    TestType.DETAILED_ANSWER: {
        "system_prompt": """\
        Ты - эксперт по созданию тестов для проверки понимания материала.
        На основе предоставленного теоретического материала модуля сгенерируй тест
        с развернутыми ответами. Тест должен содержать от 5 до 15 вопросов, в зависимости
        от объема материала. Вопросы должны требовать от студента развернутого объяснения,
        анализа, синтеза или применения концепций. Избегай вопросов,
        на которые можно ответить одним словом. Для каждого вопроса укажи:
         - текст вопроса,
         - ожидаемый ответ или ключевые моменты, которые должны быть освещены
           (опционально, для помощи в проверке),
         - подсказку (опционально),
         - баллы за вопрос (по умолчанию 1),

        Убедись, что вопросы соответствуют содержанию модуля и проверяют глубокое понимание,
        а не простое воспроизведение.
        """,
        "response_format": ToolStrategy(DetailedAnswerTest),
    }
}


async def call_knowledge_tester(test_type: TestType, module: Module) -> AnyKnowledgeTest:
    """Вызвать агента для генерации тестирования"""

    agent = create_agent(model=model, **config.get(test_type, {}))
    prompt_template = (
        "## Теоретический материал пройденного модуля:\n\n"
        "<THEORY>"
        f"{get_module_context(module)}\n"
        f"</THEORY>"
    )
    result = await agent.ainvoke({"messages": [("human", prompt_template)]})
    return result["structured_response"]
