from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    File,
    Form,
    UploadFile,
    status,
    Query,
    HTTPException,
)
from fastapi.responses import FileResponse
from pydantic import BaseModel

from app.db.models import User
from app.dependencies import (
    get_current_user,
    get_document_service,
    get_user_repository,
)
from app.repositories.user_repository import UserRepository
from app.schemas.document import DocumentResponse
from app.services.document_service import DocumentService
from app.utils.jwt import decode_access_token

router = APIRouter(
    prefix="/documents",
    tags=["Documents"],
)


@router.post(
    "/upload",
    response_model=DocumentResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_document(
    background_tasks: BackgroundTasks,
    title: str = Form(...),
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    service: DocumentService = Depends(get_document_service),
):

    return await service.upload(
        user_id=current_user.id,
        title=title,
        file=file,
        background_tasks=background_tasks,
    )


@router.get(
    "",
    response_model=list[DocumentResponse],
)
async def list_documents(
    is_deleted: bool = False,
    current_user: User = Depends(get_current_user),
    service: DocumentService = Depends(get_document_service),
):

    return await service.list(
        user_id=current_user.id,
        is_deleted=is_deleted,
    )


@router.get(
    "/{document_id}",
    response_model=DocumentResponse,
)
async def get_document(
    document_id: int,
    current_user: User = Depends(get_current_user),
    service: DocumentService = Depends(get_document_service),
):

    return await service.get(
        document_id=document_id,
        user_id=current_user.id,
    )


async def get_user_from_query(
    token: str = Query(None),
    repository: UserRepository = Depends(get_user_repository),
) -> User:
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    try:
        payload = decode_access_token(token)
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="Not authenticated")
        user = await repository.get_by_id(int(user_id))
        if not user:
            raise HTTPException(status_code=401, detail="Not authenticated")
        return user
    except Exception:
        raise HTTPException(status_code=401, detail="Not authenticated")


@router.get(
    "/{document_id}/download",
)
async def download_document(
    document_id: int,
    current_user: User = Depends(get_user_from_query),
    service: DocumentService = Depends(get_document_service),
):
    document = await service.get(
        document_id=document_id,
        user_id=current_user.id,
    )
    import mimetypes
    media_type = document.mime_type
    if not media_type or media_type == 'application/octet-stream':
        guessed_type, _ = mimetypes.guess_type(document.original_filename or "")
        if guessed_type:
            media_type = guessed_type
            
    return FileResponse(
        path=document.storage_path,
        filename=document.original_filename,
        media_type=media_type,
        content_disposition_type="inline"
    )


@router.delete(
    "/{document_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_document(
    document_id: int,
    hard: bool = Query(False),
    current_user: User = Depends(get_current_user),
    service: DocumentService = Depends(get_document_service),
):

    await service.delete(
        document_id=document_id,
        user_id=current_user.id,
        hard=hard,
    )

class BulkDeleteRequest(BaseModel):
    document_ids: list[int]
    hard: bool = False

@router.post(
    "/bulk-delete",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def bulk_delete_documents(
    request: BulkDeleteRequest,
    current_user: User = Depends(get_current_user),
    service: DocumentService = Depends(get_document_service),
):
    for doc_id in request.document_ids:
        await service.delete(
            document_id=doc_id,
            user_id=current_user.id,
            hard=request.hard,
        )