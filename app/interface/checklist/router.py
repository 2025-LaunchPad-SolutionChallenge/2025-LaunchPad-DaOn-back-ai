from datetime import date, timedelta
from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.dependencies import get_db
from app.common.dependencies import get_current_user
from app.domain.checklist import service as checklist_service
from app.infrastructure.models.checklist_model import ChecklistItemModel
from app.infrastructure.models.recovery_model import RecoveryOutputModel
from app.infrastructure.repositories.checklist_repository import SQLChecklistRepository
from app.infrastructure.repositories.disaster_repository import SQLDisasterRepository
from app.interface.checklist.schema import (
    ChecklistGenerateRequest,
    ChecklistGenerateResponse,
    GeneratedItemInfo,
)

router = APIRouter(prefix="/checklists", tags=["checklists"])


@router.post("/ai-generate", response_model=ChecklistGenerateResponse)
async def generate_ai_checklist(
    req: ChecklistGenerateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: dict[str, Any] = Depends(get_current_user),
) -> ChecklistGenerateResponse:
    uid = req.user_disaster_id

    # 재난 온보딩 정보
    disaster_repo = SQLDisasterRepository(db)
    impact_full = await disaster_repo.get_impact_full(uid)

    # 현재 회복 단계
    recovery_stage = await _get_recovery_stage(db, uid)

    # 주간 달성률
    weekly_progress = await _get_weekly_progress(db, uid)

    checklist_repo = SQLChecklistRepository(db)
    items = await checklist_service.generate_ai_checklist(
        repo=checklist_repo,
        impact_full=impact_full,
        user_disaster_id=uid,
        target_date=req.target_date,
        recovery_stage=recovery_stage,
        weekly_progress=weekly_progress,
    )

    return ChecklistGenerateResponse(
        items=[
            GeneratedItemInfo(
                checklist_item_id=item.checklist_item_id,
                title=item.title,
                priority=item.priority,
                item_source_type=item.item_source_type,
            )
            for item in items
        ]
    )


async def _get_recovery_stage(session: AsyncSession, user_disaster_id: int) -> str:
    result = await session.execute(
        select(RecoveryOutputModel)
        .where(RecoveryOutputModel.user_disaster_id == user_disaster_id)
        .order_by(RecoveryOutputModel.state_date.desc())
        .limit(1)
    )
    output = result.scalar_one_or_none()
    return output.predicted_stage if output else "CHAOS"


async def _get_weekly_progress(session: AsyncSession, user_disaster_id: int) -> float:
    seven_ago = date.today() - timedelta(days=7)

    total_result = await session.execute(
        select(func.count()).where(
            ChecklistItemModel.user_disaster_id == user_disaster_id,
            ChecklistItemModel.checklist_date >= seven_ago,
        )
    )
    total = total_result.scalar() or 0
    if total == 0:
        return 0.0

    done_result = await session.execute(
        select(func.count()).where(
            ChecklistItemModel.user_disaster_id == user_disaster_id,
            ChecklistItemModel.checklist_date >= seven_ago,
            ChecklistItemModel.is_completed == True,
        )
    )
    done = done_result.scalar() or 0
    return done / total
