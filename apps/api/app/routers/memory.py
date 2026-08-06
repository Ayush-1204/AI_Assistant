from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.models.memory import Memory
from app.db.models.user import User
from app.dependencies import get_current_user, get_db

router = APIRouter(
    prefix="/memory",
    tags=["Memory"],
)

@router.get("", response_model=list[dict])
async def get_memories(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Fetch all explicit personalized memories for the current user.
    """
    try:
        result = await db.execute(
            select(Memory)
            .where(Memory.user_id == current_user.id)
            .order_by(Memory.created_at.desc())
        )
        memories = result.scalars().all()
        
        return [
            {
                "id": m.id,
                "category": m.category,
                "key": m.key,
                "value": m.value,
                "created_at": m.created_at.isoformat() if m.created_at else None,
                "updated_at": m.updated_at.isoformat() if m.updated_at else None,
            }
            for m in memories
        ]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch memories: {str(e)}"
        )
