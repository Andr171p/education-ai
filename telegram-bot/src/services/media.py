from uuid import uuid4

import magic

from src.core import schemas
from src.database import crud, models
from src.settings import MEDIA_DIR
from src.storage import upload_file


async def upload(user_id: int, filename: str, data: bytes) -> schemas.Attachment:
    file_id = uuid4()
    user_dir = MEDIA_DIR / f"{user_id}"
    user_dir.mkdir(parents=True, exist_ok=True)
    filepath = user_dir / f"{file_id}.{filename.rsplit(".", maxsplit=1)[-1]}"
    mime_type = magic.from_buffer(data, mime=True)
    attachment = schemas.Attachment(
        id=file_id,
        original_filename=filename,
        filepath=str(filepath),
        mime_type=mime_type,
        size=len(data)
    )
    file = schemas.File(
        path=str(filepath),
        size=len(data),
        mime_type=mime_type,
        data=data,
        uploaded_at=attachment.uploaded_at
    )
    await upload_file(file)
    await crud.create(attachment, model_class=models.Attachment)
    return attachment
