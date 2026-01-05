import asyncio
import logging

import aiofiles
from langchain_core.messages import HumanMessage

from src.ai_agents.course_structure_designer import agent
from src.core import schemas
from src.services import media


async def main() -> None:
    user_id = 1779915071
    attachments: list[schemas.Attachment] = []
    files = ["Лекция 1.pdf", "Лекция 2.pdf", "Лекция 3.pptx"]
    for file in files:
        async with aiofiles.open(file, mode="rb") as f:
            data = await f.read()
            attachment = await media.upload(user_id=user_id, filename=file, data=data)
            attachments.append(attachment)

    teacher_inputs = schemas.TeacherInputs(
        user_id=user_id,
        discipline="Системы Искусственного интеллекта",
        comment="""Продумай 5 тестов и 7 лабораторных работ для студентов IT направлений 3 курса
        Тюменского Индустриального университета""",
        attachments=[attachment.id for attachment in attachments],
    )
    prompt = teacher_inputs.to_prompt()
    initial_state = {"teacher_prompt": prompt, "messages": [HumanMessage(content=prompt)]}
    result = await agent.ainvoke(
        initial_state, config={"configurable": {"thread_id": "12345"}}
    )
    print(result)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
