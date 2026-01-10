from uuid import uuid4

from ..core import enums, schemas
from ..database import crud, models
from ..rag.attached_materials import index_attachments


async def confirm_creation(teacher_inputs: schemas.TeacherInputs) -> schemas.Task:
    course_id = uuid4()
    course_creation_task = schemas.Task(
        status=enums.TaskStatus.PENDING, resource_id=course_id
    )
    await crud.create(course_creation_task, model_class=models.Task)
    await index_attachments(course_id=course_id, attachment_ids=teacher_inputs.attachments)
    return await crud.refresh(
        course_creation_task.id,
        model_class=models.Task,
        schema_class=schemas.Task,
        status=enums.TaskStatus.RUNNING,
    )
