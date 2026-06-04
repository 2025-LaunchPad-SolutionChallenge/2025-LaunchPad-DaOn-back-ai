from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.dependencies import get_db
from app.common.dependencies import get_current_user
from app.domain.home import service as home_service
from app.infrastructure.repositories.home_repository import SQLHomeRepository
from app.interface.home.schema import DailyStatusRequest, DailyStatusResponse

router = APIRouter(prefix="/home", tags=["home"])


@router.post("/daily-status", response_model=DailyStatusResponse)
async def submit_daily_status(
    req: DailyStatusRequest,
    db: AsyncSession = Depends(get_db),
    current_user: dict[str, Any] = Depends(get_current_user),
) -> DailyStatusResponse:
    repo = SQLHomeRepository(db)
    saved = await home_service.submit_daily_status(
        repo=repo,
        firebase_uid=current_user["firebase_uid"],
        emotion_score=req.emotion_score,
        condition_score=req.energy_score,
        action_score=req.activity_score,
        change_score=req.recovery_score,
        need_score=req.need_score,
    )
    return DailyStatusResponse(
        daily_check_id=saved.daily_check_id,
        total_score=saved.total_score,
        message="상태 체크 완료",
    )
