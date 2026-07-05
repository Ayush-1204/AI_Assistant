from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.dependencies import get_db, get_current_user
from app.db.models.user import User
from app.db.models.device import Device
from pydantic import BaseModel

router = APIRouter(prefix="/devices", tags=["Devices"])

class RegisterDeviceReq(BaseModel):
    platform: str
    device_token: str

@router.post("/register")
async def register(req: RegisterDeviceReq, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Device).where(Device.device_token == req.device_token))
    existing = result.scalar_one_or_none()
    
    if existing:
        existing.user_id = user.id
        existing.active = True
    else:
        new_device = Device(user_id=user.id, platform=req.platform, device_token=req.device_token)
        db.add(new_device)
        
    await db.commit()
    return {"status": "ok"}

@router.post("/unregister")
async def unregister(req: RegisterDeviceReq, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Device).where(Device.device_token == req.device_token, Device.user_id == user.id))
    existing = result.scalar_one_or_none()
    
    if existing:
        existing.active = False
        await db.commit()
        
    return {"status": "ok"}
