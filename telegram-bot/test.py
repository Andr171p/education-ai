import asyncio
import logging
from uuid import UUID

import aiofiles
from langchain_core.messages import HumanMessage

from src.ai_agents.course_structure_planner import plan_course_structure
from src.core import schemas
from src.services import media


async def main() -> None:
    user_id = 1779915071
    """attachments: list[schemas.Attachment] = []
    files = ["Лекция 1.pdf", "Лекция 2.pdf", "Лекция 3.pptx"]
    for file in files:
        async with aiofiles.open(file, mode="rb") as f:
            data = await f.read()
            attachment = await media.upload(user_id=user_id, filename=file, data=data)
            attachments.append(attachment)"""

    teacher_inputs = schemas.TeacherInputs(
        user_id=user_id,
        discipline="Системы Искусственного интеллекта",
        comment="""Курс рассчитан на студентов 3 курса IT-направления
        Тюменского Индустриального университета, длительность 1 семестр""",
        attachments=[UUID("1f27cdba-95ae-43e7-bf9f-aaf742c6c88f")],
    )
    print(await plan_course_structure(teacher_inputs))


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
