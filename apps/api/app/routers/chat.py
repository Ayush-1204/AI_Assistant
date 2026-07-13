from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse

from app.dependencies import (
    get_ai_service,
    get_current_user,
)
from app.schemas.chat import ChatRequest, ChatResponse
from app.services.ai.ai_service import AIService

router = APIRouter(
    prefix="/chat",
    tags=["Chat"],
)


@router.post(
    "",
    response_model=ChatResponse,
)
async def chat(
    request: ChatRequest,
    fastapi_req: Request,
    current_user=Depends(get_current_user),
    service: AIService = Depends(get_ai_service),
):
    lat = fastapi_req.headers.get('X-User-Lat')
    lon = fastapi_req.headers.get('X-User-Lon')
    lat = float(lat) if lat else None
    lon = float(lon) if lon else None

    response, citations, metadata_obj = await service.chat(
        user_id=current_user.id,
        conversation_id=request.conversation_id,
        prompt=request.message,
        location_lat=lat,
        location_lon=lon,
        is_regenerate=request.is_regenerate,
        images=request.images,
        intent=request.intent,
    )

    return ChatResponse(
        response=response,
        citations=citations,
        metadata=metadata_obj
    )


@router.post(
    "/stream",
)
async def stream_chat_route(
    request: ChatRequest,
    fastapi_req: Request,
    current_user=Depends(get_current_user),
    service: AIService = Depends(get_ai_service),
):
    from fastapi import HTTPException

    from app.security.injection_scanner import InjectionScanner
    
    scan_res = InjectionScanner().scan(request.message)
    if not scan_res["is_clean"]:
        raise HTTPException(status_code=400, detail=f"Prompt rejected: {scan_res['findings']}")
        
    lat = fastapi_req.headers.get('X-User-Lat')
    lon = fastapi_req.headers.get('X-User-Lon')
    lat = float(lat) if lat else None
    lon = float(lon) if lon else None

    return StreamingResponse(
        service.stream_chat(
            user_id=current_user.id,
            conversation_id=request.conversation_id,
            prompt=request.message,
            location_lat=lat,
            location_lon=lon,
            is_regenerate=request.is_regenerate,
            images=request.images,
            intent=request.intent,
        ),
        media_type="text/event-stream"
    )