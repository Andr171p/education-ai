from fastapi import APIRouter, File, Header, UploadFile, status

from ....core.schemas import Attachment
from ....services import media

router = APIRouter(prefix="/media", tags=["Media"])


@router.post(
    path="/upload",
    status_code=status.HTTP_201_CREATED,
    response_model=Attachment,
    summary="Загрузка медиа на сервер"
)
async def upload(
        user_id: str = Header(alias="X-User-ID"), file: UploadFile = File(...)
) -> Attachment:
    return await media.upload(
        user_id=int(user_id), filename=file.filename, data=await file.read()
    )
