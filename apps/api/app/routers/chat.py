import json
from typing import Any

from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from app.dependencies import (
    get_ai_service,
    get_current_user,
    get_db,
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
    db = Depends(get_db),
):
    lat = fastapi_req.headers.get('X-User-Lat')
    lon = fastapi_req.headers.get('X-User-Lon')
    lat = float(lat) if lat else None
    lon = float(lon) if lon else None

    if lat is not None and lon is not None:
        current_user.last_known_lat = lat
        current_user.last_known_lon = lon
        db.add(current_user)
        await db.commit()

    response, citations, metadata_obj = await service.chat(
        user_id=current_user.id,
        conversation_id=request.conversation_id,
        prompt=request.message,
        location_lat=lat,
        location_lon=lon,
        is_regenerate=request.is_regenerate,
        images=request.images,
        intent=request.intent,
        user_name=current_user.full_name,
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
    db = Depends(get_db),
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

    if lat is not None and lon is not None:
        current_user.last_known_lat = lat
        current_user.last_known_lon = lon
        db.add(current_user)
        await db.commit()

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
            user_name=current_user.full_name,
            fastapi_request=fastapi_req
        ),
        media_type="text/event-stream"
    )


class ApprovePlanRequest(BaseModel):
    conversation_id: int
    approved_steps: list[dict[str, Any]]


@router.post("/approve-plan")
async def approve_plan(
    request: ApprovePlanRequest,
    current_user=Depends(get_current_user),
    service: AIService = Depends(get_ai_service),
):
    """Execute a user-approved plan and stream the synthesized response."""
    async def _stream():
        try:
            from app.schemas.tool import ToolRequest
            from app.services.ai.tools.orchestrator import ToolOrchestrator

            strategy = await service._get_strategy()
            tool_orch: ToolOrchestrator = service.tool_orchestrator
            context = {"user_id": current_user.id, "conversation_id": request.conversation_id}

            tool_responses = []
            for step in request.approved_steps:
                args = step.get("arguments", {})
                args["_confirmed"] = True
                
                req = ToolRequest(
                    id=step.get("id", "approved"),
                    name=step["name"],
                    arguments=args,
                )
                yield f"data: {json.dumps({'type': 'tool', 'name': f'Running {req.name}...'})}\n\n"
                try:
                    from app.services.ai.tools.orchestrator import ToolOrchestrator  # noqa: F811
                    res = await tool_orch.execute_tool(req, context)
                    tool_responses.append(res)
                except Exception as e:
                    from app.schemas.tool import ToolResponse
                    tool_responses.append(ToolResponse(id=req.id, name=req.name, content=str(e), is_error=True))

            # Build a follow-up prompt for the LLM to synthesize the results
            results_summary = "\n".join(
                [f"Tool `{r.name}` returned: {r.content[:1000]}" for r in tool_responses]
            )
            synthesis_prompt = f"The user approved the execution plan. Here are the results:\n{results_summary}\n\nSynthesize a concise, helpful response."

            # Stream the synthesis
            from app.services.ai.planner.planner import Planner
            from app.services.ai.planner.executor import AgentExecutor
            planner = Planner(service.provider, strategy, intent="general")
            executor = AgentExecutor(planner, tool_orch, strategy, intent="general")

            messages, _ = await service.context_builder.build(
                user_id=current_user.id,
                conversation_id=request.conversation_id,
                query=synthesis_prompt,
            )
            tools_payload = strategy.get_tools_for_provider()

            from app.schemas.message import MessageCreate, MessageRole
            
            db_results_content = ""
            for r in tool_responses:
                db_results_content += f"Tool execution result for:\n<tool_call>\n{{\"name\": \"{r.name}\", \"args\": {{}}}}\n</tool_call>\n\n<tool_response>\n{r.content[:8000]}\n</tool_response>\n"
            
            if tool_responses:
                await service.message_service.create(
                    request.conversation_id,
                    MessageCreate(role=MessageRole.USER, content=db_results_content)
                )

            final_synthesis = ""
            async for chunk in executor.stream_run(synthesis_prompt, context, messages, tools_payload):
                if chunk.startswith("data: ") and '"delta"' in chunk:
                    try:
                        delta = json.loads(chunk[6:])['delta']
                        final_synthesis += delta
                    except:
                        pass
                yield chunk
                
            if final_synthesis:
                await service.message_service.create(
                    request.conversation_id,
                    MessageCreate(role=MessageRole.ASSISTANT, content=final_synthesis)
                )

        except Exception as e:
            yield f"data: {json.dumps({'type': 'content', 'delta': f'Plan execution failed: {e}'})}\n\n"
            yield "data: [DONE]\n\n"

    return StreamingResponse(_stream(), media_type="text/event-stream")