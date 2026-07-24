import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.scheduled_job import JobStatus, ScheduledJob
from app.db.session import AsyncSessionLocal
from app.dependencies import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/scheduled-tasks", tags=["Scheduled Tasks"])


class CreateScheduledTaskRequest(BaseModel):
    label: str
    directive: str
    cron_expression: str | None = None
    run_at: datetime | None = None
    timezone_offset_minutes: int | None = None


class ScheduledTaskResponse(BaseModel):
    id: int
    label: str | None
    directive: str | None
    cron_expression: str | None
    scheduled_time: datetime
    next_run_at: datetime | None
    status: str
    is_enabled: bool
    created_at: datetime

    class Config:
        from_attributes = True


def _compute_next_run(cron_expr: str, now: datetime) -> datetime | None:
    try:
        from croniter import croniter  # type: ignore
        cron = croniter(cron_expr, now)
        return cron.get_next(datetime)
    except Exception:
        return None


@router.get("", response_model=list[ScheduledTaskResponse])
async def list_scheduled_tasks(
    current_user=Depends(get_current_user),
):
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(ScheduledJob)
            .where(
                ScheduledJob.user_id == current_user.id,
                ScheduledJob.is_user_defined == True,  # noqa: E712
            )
            .order_by(ScheduledJob.created_at.desc())
        )
        return result.scalars().all()


@router.post("", response_model=ScheduledTaskResponse, status_code=201)
async def create_scheduled_task(
    body: CreateScheduledTaskRequest,
    current_user=Depends(get_current_user),
):
    from datetime import timezone, timedelta
    
    if body.timezone_offset_minutes is not None:
        user_tz = timezone(timedelta(minutes=body.timezone_offset_minutes))
    else:
        user_tz = timezone.utc

    now = datetime.now(user_tz)

    if body.cron_expression:
        next_run = _compute_next_run(body.cron_expression, now)
        if not next_run:
            raise HTTPException(status_code=400, detail="Invalid cron_expression. Use 5-field cron syntax.")
        scheduled_time = next_run
    elif body.run_at:
        if body.run_at <= now:
            raise HTTPException(status_code=400, detail="run_at must be a future datetime.")
        scheduled_time = body.run_at
    else:
        raise HTTPException(status_code=400, detail="Provide either cron_expression or run_at.")

    async with AsyncSessionLocal() as db:
        job = ScheduledJob(
            user_id=current_user.id,
            label=body.label,
            recurring_action=body.directive,
            cron_expression=body.cron_expression,
            scheduled_time=scheduled_time,
            next_run_at=scheduled_time if body.cron_expression else None,
            status=JobStatus.PENDING,
            is_user_defined=True,
            is_enabled=True,
        )
        db.add(job)
        await db.commit()
        await db.refresh(job)
        logger.info(f"[ScheduledTasks] User {current_user.id} created job '{body.label}' (id={job.id})")
        return job


@router.delete("/{task_id}", status_code=204)
async def delete_scheduled_task(
    task_id: int,
    current_user=Depends(get_current_user),
):
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(ScheduledJob).where(
                ScheduledJob.id == task_id,
                ScheduledJob.user_id == current_user.id,
            )
        )
        job = result.scalar_one_or_none()
        if not job:
            raise HTTPException(status_code=404, detail="Scheduled task not found.")
        await db.delete(job)
        await db.commit()


@router.patch("/{task_id}/toggle", response_model=ScheduledTaskResponse)
async def toggle_scheduled_task(
    task_id: int,
    current_user=Depends(get_current_user),
):
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(ScheduledJob).where(
                ScheduledJob.id == task_id,
                ScheduledJob.user_id == current_user.id,
            )
        )
        job = result.scalar_one_or_none()
        if not job:
            raise HTTPException(status_code=404, detail="Scheduled task not found.")
        job.is_enabled = not job.is_enabled
        await db.commit()
        await db.refresh(job)
        return job
