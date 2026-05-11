import asyncio
import logging
import os

from dotenv import load_dotenv

from src.infra.db.conn import session_factory
from src.infra.db.repos import CourseRepository, StudentRepository
from src.settings import ENV_PATH

load_dotenv(ENV_PATH)

TEACHER_ID = os.getenv("TEACHER_ID")

logger = logging.getLogger(__name__)


async def main() -> None:
    student_id = int(TEACHER_ID)
    async with session_factory() as session:
        student_repo = StudentRepository(session)
        course_repo = CourseRepository(session)
        group = await student_repo.get_student_group(student_id)
        course = await course_repo.read(group.course_id)
        progress = await student_repo.get_learning_progress(student_id)
        last_module_id = course.modules[-1].id
        for module in course.modules:
            progress.switch_to_next_module(module.id)
            if module.id == last_module_id:
                progress.increment_test_score(30)
            else:
                progress.increment_test_score(80)
                progress.increment_assignment_score(1)
        await student_repo.refresh_learning_progress(progress)
    logger.info("Course open successfully for teacher")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
