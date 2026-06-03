from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.dependencies import get_db
from app.common.security import get_current_user
from app.domain.disaster import service as disaster_service
from app.infrastructure.repositories.disaster_repository import SQLDisasterRepository
from app.interface.disaster.schema import (
    ContextRequest,
    ContextResponse,
    OnboardingRequest,
    OnboardingResponse,
)

router = APIRouter(tags=["disasters"])


@router.post("/onboarding", response_model=OnboardingResponse)
async def submit_onboarding(
    req: OnboardingRequest,
    db: AsyncSession = Depends(get_db),
    current_user: dict[str, Any] = Depends(get_current_user),
) -> OnboardingResponse:
    repo = SQLDisasterRepository(db)
    saved = await disaster_service.process_onboarding(
        repo=repo,
        disaster_id=req.disaster_id,
        disaster_type=req.disaster_type.value,
        safety_status=req.safety_status.value if req.safety_status else None,
        residence_status=req.residence_status.value,
        injury_level=req.injury_level.value,
        damages=req.damages,
        flood_level=req.flood_level.value if req.flood_level else None,
        water_drain_status=req.water_drain_status.value if req.water_drain_status else None,
        aftershock_feeling=req.aftershock_feeling.value if req.aftershock_feeling else None,
        fire_damage_scope=req.fire_damage_scope.value if req.fire_damage_scope else None,
        smoke_inhalation=req.smoke_inhalation.value if req.smoke_inhalation else None,
    )
    return OnboardingResponse(
        impact_id=saved.impact_id,
        onboarding_risk_level=saved.onboarding_risk_level,
        message="피해 상황이 등록되었습니다",
    )


@router.post("/checklists/context", response_model=ContextResponse)
async def submit_context(
    req: ContextRequest,
    db: AsyncSession = Depends(get_db),
    current_user: dict[str, Any] = Depends(get_current_user),
) -> ContextResponse:
    repo = SQLDisasterRepository(db)
    await disaster_service.update_checklist_context(
        repo=repo,
        user_disaster_id=req.user_disaster_id,
        can_go_out=req.user_condition.can_go_out,
        available_time=req.user_condition.available_time.value,
    )
    return ContextResponse(message="상황 입력 완료")
