
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.services.ai.skills.manager import SkillManager
from app.services.ai.tools.registry import ToolRegistry

router = APIRouter(prefix="/skills", tags=["Skills"])

# Create a master, centralized registry for dynamic loading
GLOBAL_SKILL_REGISTRY = ToolRegistry()
skill_manager = SkillManager(GLOBAL_SKILL_REGISTRY)

class SkillDownloadRequest(BaseModel):
    name: str
    url: str

class SkillSchemaResponse(BaseModel):
    name: str
    description: str
    parameters: dict

@router.post("/install", response_model=bool)
async def install_skill(request: SkillDownloadRequest):
    """Downloads a python script conforming to agentskills.io format and dynamically registers it."""
    success = await skill_manager.download_skill(request.url, request.name)
    if not success:
        raise HTTPException(status_code=400, detail=f"Failed to install skill {request.name}")
    return True

@router.get("/list", response_model=list[SkillSchemaResponse])
async def list_installed_skills():
    """Lists all dynamically installed skills currently mapped to the Orchestrator."""
    return GLOBAL_SKILL_REGISTRY.get_all_schemas()
