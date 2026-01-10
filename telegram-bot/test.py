import asyncio
import json
import logging

import aiofiles

from src.ai_agents.course_structure_planner import PlannerContext, agent
from src.core import enums, schemas
from src.services import courses as courses_service
from src.services import media as media_service

logger = logging.getLogger(__name__)


async def main() -> None:
    user_id = 1779915071
    attachments: list[schemas.Attachment] = []
    files = ["Лекция 1.pdf", "Лекция 2.pdf", "Лекция 3.pptx"]
    for file in files:
        async with aiofiles.open(file, mode="rb") as f:
            data = await f.read()
            attachment = await media_service.upload(user_id=user_id, filename=file, data=data)
            attachments.append(attachment)

    teacher_inputs = schemas.TeacherInputs(
        user_id=user_id,
        discipline="Системы Искусственного интеллекта",
        target_audience="Студенты 3 курса IT-направлений Тюменского Индустриального Университета",
        difficulty_level=enums.DifficultyLevel.BEGINNER,
        comment="Курс идёт 1 семестр, в качестве языка программирования используй Python",
        attachments=[attachment.id for attachment in attachments],
    )
    task = await courses_service.confirm_creation(teacher_inputs)
    result = await agent.ainvoke(
        {"messages": []}, context=PlannerContext(
            user_id=user_id, course_id=task.resource_id, teacher_inputs=teacher_inputs
        )
    )
    print(result["structured_response"])
    with open("new_plan.json", "w", encoding="utf-8") as f:
        json.dump(result["structured_response"].model_dump_json(), f, indent=4, ensure_ascii=False)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
