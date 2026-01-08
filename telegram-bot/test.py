import asyncio
import json
import logging
from uuid import UUID

from src.ai_agents.course_structure_planner import CourseStructurePlan, plan_course_structure
from src.ai_agents.module_generator import content_block_generator_agent
from src.core import schemas
from src.services import media

logger = logging.getLogger(__name__)


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
        Тюменского Индустриального университета, длительность 1 семестр,
        в качестве языка программирования используй Python
        """,
        attachments=[UUID("1f27cdba-95ae-43e7-bf9f-aaf742c6c88f")],
    )
    # course_structure_plan = await plan_course_structure(teacher_inputs)
    with open("course_plan_1.json", encoding="utf-8") as f:
        plan_json = json.load(f)
    course_structure_plan = CourseStructurePlan.model_validate_json(plan_json)
    content_blocks_strategy = course_structure_plan.module_plans[0].content_blocks_strategy
    first_key = next(iter(content_blocks_strategy))
    content_block = await content_block_generator_agent.ainvoke(
        input={"messages": []},
        context={
            "discipline": teacher_inputs.discipline,
            "module_title": course_structure_plan.module_plans[0].title,
            "module_description": course_structure_plan.module_plans[0].description,
            "module_order": course_structure_plan.module_plans[0].order,
            "module_key_topics": course_structure_plan.module_plans[0].key_topics,
            "module_learning_objectives": course_structure_plan.module_plans[0].learning_objectives,
            "thoughts": course_structure_plan.module_plans[0].thoughts,
            "block_type": first_key,
            "block_plan": content_blocks_strategy.get(first_key),
        }
    )
    print(content_block)
    with open("course_plan_1.json", "w", encoding="utf-8") as f:
        json.dump(course_structure_plan.model_dump_json(), f, ensure_ascii=False, indent=4)
    with open("content_block.json", "w", encoding="utf-8") as f:
        json.dump(content_block, f, ensure_ascii=False, indent=4)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
