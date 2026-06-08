from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.dependencies import get_db
from app.common.dependencies import get_current_user
from app.common.exceptions import AppException
from app.domain.disaster import service as disaster_service
from app.infrastructure.models.disaster_model import UserDisasterModel
from app.infrastructure.models.recovery_model import RecoveryOutputModel
from app.infrastructure.repositories.disaster_repository import SQLDisasterRepository
from app.interface.disaster.schema import (
    OnboardingRequest,
    OnboardingResponse,
    RecoveryStageResponse,
)

router = APIRouter(prefix="/disasters", tags=["disasters"])


@router.post("/onboarding", response_model=OnboardingResponse)
async def submit_onboarding(
    req: OnboardingRequest,
    db: AsyncSession = Depends(get_db),
    current_user: dict[str, Any] = Depends(get_current_user),
) -> OnboardingResponse:
    repo = SQLDisasterRepository(db)
    user_id = int(current_user["sub"])
    saved = await disaster_service.process_onboarding(
        repo=repo,
        user_id=user_id,
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
        user_disaster_id=saved.user_disaster_id,
        impact_id=saved.impact_id,
        onboarding_risk_level=saved.onboarding_risk_level,
        message="피해 상황이 등록되었습니다",
    )


_STAGE_INFO = {
    "CHAOS":      (1, "CHAOS",              "혼란기",     "상황을 받아들이는 것만으로도 버거운 상태예요."),
    "STAGNANT":   (2, "STAGNANT",           "정체기",     "조금은 익숙해졌지만, 앞으로 나아가긴 어려운 상태예요."),
    "ATTEMPTING": (3, "ATTEMPTING",         "시도기",     "조심스럽게 다시 움직이기 시작한 상태예요."),
    "STABLE":     (4, "STABLE",             "안정기",     "일상이 어느 정도 회복되고 있는 상태예요."),
    "MAINTAINED": (5, "RECOVERY_MAINTAINED","회복 유지기", "회복된 일상을 안정적으로 유지하고 있어요."),
}


@router.get("/{disaster_id}/recovery/stage", response_model=RecoveryStageResponse)
async def get_recovery_stage(
    disaster_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict[str, Any] = Depends(get_current_user),
) -> RecoveryStageResponse:
    user_id = int(current_user["sub"])

    result = await db.execute(
        select(UserDisasterModel).where(UserDisasterModel.user_disaster_id == disaster_id)
    )
    user_disaster = result.scalar_one_or_none()

    if user_disaster is None:
        raise AppException(status_code=404, code=404, message="해당 disasterId가 존재하지 않습니다.", error_key="DISASTER_NOT_FOUND")
    if user_disaster.user_id != user_id:
        raise AppException(status_code=403, code=403, message="접근 권한이 없습니다.", error_key="FORBIDDEN")

    result = await db.execute(
        select(RecoveryOutputModel)
        .where(RecoveryOutputModel.user_disaster_id == disaster_id)
        .order_by(RecoveryOutputModel.state_date.desc())
        .limit(1)
    )
    output = result.scalar_one_or_none()
    stage_code = output.predicted_stage if output else "CHAOS"

    stage_id, code, name, description = _STAGE_INFO.get(stage_code, _STAGE_INFO["CHAOS"])
    return RecoveryStageResponse(
        stage_id=stage_id,
        stage_code=code,
        stage_name=name,
        description=description,
    )


