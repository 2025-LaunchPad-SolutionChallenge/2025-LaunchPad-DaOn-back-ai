from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Query

from app.common.dependencies import get_current_access_payload, get_disaster_service
from app.common.swagger import error_responses
from app.domain.disaster.entity import DisasterDetail, DisasterListPage
from app.domain.disaster.service import DisasterService
from app.interface.disaster.schema import (
    DisasterCloseRequest,
    DisasterCloseResponse,
    DisasterDetailResponse,
    DisasterImpactResponse,
    DisasterListItemResponse,
    DisasterListResponse,
    DisasterPatchRequest,
    DisasterPatchResponse,
    DisasterTypeResponse,
    LocationResponse,
    OnboardingRequest,
    OnboardingResponse,
    RecoveryGraphPointResponse,
    RecoveryGraphResponse,
    RecoveryProgressResponse,
    RecoveryStageDetailResponse,
    RecoveryStageResponse,
)

router = APIRouter(prefix="/disasters", tags=["disasters"])


def _to_list_response(page_data: DisasterListPage) -> DisasterListResponse:
    return DisasterListResponse(
        content=[
            DisasterListItemResponse(
                userDisasterId=item.user_disaster_id,
                title=item.title,
                disasterTypeCode=item.disaster_type_code,
                disasterTypeName=item.disaster_type_name,
                status=item.status,
                occurredAt=item.occurred_at,
                endedAt=item.ended_at,
                recoveryStage=RecoveryStageResponse(
                    stageCode=item.recovery_stage.stage_code,
                    stageName=item.recovery_stage.stage_name,
                ),
                recoveryProgress=item.recovery_progress,
            )
            for item in page_data.content
        ],
        page=page_data.page,
        size=page_data.size,
        totalElements=page_data.total_elements,
    )


def _to_detail_response(detail: DisasterDetail) -> DisasterDetailResponse:
    location = None
    if detail.latitude is not None or detail.longitude is not None or detail.address is not None:
        location = LocationResponse(
            latitude=detail.latitude,
            longitude=detail.longitude,
            address=detail.address,
        )
    return DisasterDetailResponse(
        userDisasterId=detail.user_disaster_id,
        title=detail.title,
        disasterType=DisasterTypeResponse(
            disasterTypeId=detail.disaster_type.disaster_type_id,
            disasterCode=detail.disaster_type.disaster_code,
            name=detail.disaster_type.name,
        ),
        status=detail.status,
        occurredAt=detail.occurred_at,
        endedAt=detail.ended_at,
        location=location,
        recoveryStage=RecoveryStageResponse(
            stageCode=detail.recovery_stage.stage_code,
            stageName=detail.recovery_stage.stage_name,
        ),
        recoveryProgress=detail.recovery_progress,
        impact=(
            DisasterImpactResponse(
                safetyStatus=detail.impact.safety_status,
                residenceStatus=detail.impact.residence_status,
                injuryLevel=detail.impact.injury_level,
                canGoOut=detail.impact.can_go_out,
                availableTime=detail.impact.available_time,
            )
            if detail.impact
            else None
        ),
        detail=detail.detail,
    )


@router.get(
    "",
    response_model=DisasterListResponse,
    summary="재난 목록 조회",
    description="상태 우선순위(ACTIVE→EXPIRED→ARCHIVED) 후 등록일 최신순으로 재난 목록을 조회합니다.",
    responses=error_responses(401, 500),
)
async def list_disasters(
    page: int = Query(0, ge=0),
    size: int = Query(20, ge=1, le=100),
    payload: dict[str, Any] = Depends(get_current_access_payload),
    disaster_service: DisasterService = Depends(get_disaster_service),
) -> DisasterListResponse:
    user_id = int(payload["sub"])
    page_data = await disaster_service.get_disasters(user_id=user_id, page=page, size=size)
    return _to_list_response(page_data)


@router.post(
    "/onboarding",
    response_model=OnboardingResponse,
    status_code=201,
    summary="재난 온보딩 등록",
    description="초기 재난 영향 정보와 발생 위치(위도/경도/주소)를 등록하고 사용자 재난을 생성합니다.",
    responses=error_responses(400, 401, 500),
)
async def submit_onboarding(
    req: OnboardingRequest,
    payload: dict[str, Any] = Depends(get_current_access_payload),
    disaster_service: DisasterService = Depends(get_disaster_service),
) -> OnboardingResponse:
    user_id = int(payload["sub"])
    user_disaster_id, impact_id, onboarding_risk_level = await disaster_service.submit_onboarding(
        user_id=user_id,
        disaster_type=req.disasterType.value,
        latitude=req.latitude,
        longitude=req.longitude,
        address=req.address,
        safety_status=req.safetyStatus.value if req.safetyStatus else None,
        residence_status=req.residenceStatus.value,
        injury_level=req.injuryLevel.value,
        damages=req.damages,
        flood_level=req.floodLevel.value if req.floodLevel else None,
        water_drain_status=req.waterDrainStatus.value if req.waterDrainStatus else None,
        aftershock_feeling=req.aftershockFeeling.value if req.aftershockFeeling else None,
        fire_damage_scope=req.fireDamageScope.value if req.fireDamageScope else None,
        smoke_inhalation=req.smokeInhalation.value if req.smokeInhalation else None,
    )
    return OnboardingResponse(
        userDisasterId=user_disaster_id,
        impactId=impact_id,
        onboardingRiskLevel=onboarding_risk_level,
        message="피해 상황이 등록되었습니다",
    )


@router.get(
    "/{userDisasterId}",
    response_model=DisasterDetailResponse,
    summary="재난 상세 조회",
    description="특정 재난의 발생 위치(location), 영향(impact), 유형별 상세(detail)를 조회합니다.",
    responses=error_responses(401, 403, 404, 500),
)
async def get_disaster_detail(
    userDisasterId: int,
    payload: dict[str, Any] = Depends(get_current_access_payload),
    disaster_service: DisasterService = Depends(get_disaster_service),
) -> DisasterDetailResponse:
    user_id = int(payload["sub"])
    detail = await disaster_service.get_disaster_detail(
        user_id=user_id,
        user_disaster_id=userDisasterId,
    )
    return _to_detail_response(detail)


@router.get(
    "/{userDisasterId}/recovery/stage",
    response_model=RecoveryStageDetailResponse,
    summary="회복 단계 조회",
    description="해당 재난의 최신 회복 단계를 조회합니다.",
    responses=error_responses(401, 403, 404, 500),
)
async def get_recovery_stage(
    userDisasterId: int,
    payload: dict[str, Any] = Depends(get_current_access_payload),
    disaster_service: DisasterService = Depends(get_disaster_service),
) -> RecoveryStageDetailResponse:
    user_id = int(payload["sub"])
    stage_id, stage_code, stage_name, description = await disaster_service.get_recovery_stage_detail(
        user_id=user_id,
        user_disaster_id=userDisasterId,
    )
    return RecoveryStageDetailResponse(
        stageId=stage_id,
        stageCode=stage_code,
        stageName=stage_name,
        description=description,
    )


@router.get(
    "/{userDisasterId}/recovery-graph",
    response_model=RecoveryGraphResponse,
    summary="회복 그래프 조회",
    description="회복 출력 이력을 날짜 순으로 반환합니다.",
    responses=error_responses(401, 403, 404, 500),
)
async def get_recovery_graph(
    userDisasterId: int,
    payload: dict[str, Any] = Depends(get_current_access_payload),
    disaster_service: DisasterService = Depends(get_disaster_service),
) -> RecoveryGraphResponse:
    user_id = int(payload["sub"])
    points = await disaster_service.get_recovery_graph_points(
        user_id=user_id,
        user_disaster_id=userDisasterId,
    )
    return RecoveryGraphResponse(
        userDisasterId=userDisasterId,
        points=[
            RecoveryGraphPointResponse(date=d, recoveryScore=score, stageCode=code, stageName=name)
            for d, score, code, name in points
        ],
    )


@router.get(
    "/{userDisasterId}/recovery/progress",
    response_model=RecoveryProgressResponse,
    summary="회복 진행률 조회",
    description="재난의 현재 회복 진행률과 단계 정보를 반환합니다.",
    responses=error_responses(401, 403, 404, 500),
)
async def get_recovery_progress(
    userDisasterId: int,
    payload: dict[str, Any] = Depends(get_current_access_payload),
    disaster_service: DisasterService = Depends(get_disaster_service),
) -> RecoveryProgressResponse:
    user_id = int(payload["sub"])
    score, stage_code, stage_name, stage_description = await disaster_service.get_latest_recovery_progress(
        user_id=user_id,
        user_disaster_id=userDisasterId,
    )
    return RecoveryProgressResponse(
        userDisasterId=userDisasterId,
        recoveryScore=score,
        stageCode=stage_code,
        stageName=stage_name,
        stageDescription=stage_description,
    )


@router.patch(
    "/{userDisasterId}",
    response_model=DisasterPatchResponse,
    summary="재난 정보 수정",
    description="ACTIVE 상태 재난의 공통 정보/impact/detail을 부분 수정합니다.",
    responses=error_responses(400, 401, 403, 404, 409, 500),
)
async def patch_disaster(
    userDisasterId: int,
    req: DisasterPatchRequest,
    payload: dict[str, Any] = Depends(get_current_access_payload),
    disaster_service: DisasterService = Depends(get_disaster_service),
) -> DisasterPatchResponse:
    user_id = int(payload["sub"])
    impact_updates = None
    if req.impact is not None:
        impact_updates = {
            "safety_status": req.impact.safetyStatus,
            "residence_status": req.impact.residenceStatus,
            "injury_level": req.impact.injuryLevel,
            "can_go_out": req.impact.canGoOut,
            "available_time": req.impact.availableTime,
        }
    detail_updates = None
    if req.detail is not None:
        detail_updates = {
            "flood_level": req.detail.get("floodLevel"),
            "water_drain_status": req.detail.get("waterDrainStatus"),
            "damage_house": req.detail.get("damageHouse"),
            "damage_vehicle": req.detail.get("damageVehicle"),
            "electric_problem": req.detail.get("electricProblem"),
            "water_problem": req.detail.get("waterProblem"),
            "aftershock_feeling": req.detail.get("aftershockFeeling"),
            "building_crack": req.detail.get("buildingCrack"),
            "house_damage": req.detail.get("houseDamage"),
            "vehicle_damage": req.detail.get("vehicleDamage"),
            "roof_damage": req.detail.get("roofDamage"),
            "window_damage": req.detail.get("windowDamage"),
            "structure_damage": req.detail.get("structureDamage"),
            "fire_damage_scope": req.detail.get("fireDamageScope"),
            "smoke_inhalation": req.detail.get("smokeInhalation"),
            "soot_damage": req.detail.get("sootDamage"),
            "debris_exist": req.detail.get("debrisExist"),
        }
    await disaster_service.update_disaster(
        user_id=user_id,
        user_disaster_id=userDisasterId,
        title=req.title,
        occurred_at=req.occurredAt,
        impact_updates=impact_updates,
        detail_updates=detail_updates,
    )
    return DisasterPatchResponse(
        userDisasterId=userDisasterId,
        message="재난 정보가 수정되었습니다.",
    )


@router.patch(
    "/{userDisasterId}/close",
    response_model=DisasterCloseResponse,
    summary="재난 종료/보관 처리",
    description="ACTIVE 상태 재난을 CLOSE(EXPIRED) 또는 ARCHIVE(ARCHIVED)로 전환합니다.",
    responses=error_responses(400, 401, 403, 404, 409, 500),
)
async def close_disaster(
    userDisasterId: int,
    req: DisasterCloseRequest,
    payload: dict[str, Any] = Depends(get_current_access_payload),
    disaster_service: DisasterService = Depends(get_disaster_service),
) -> DisasterCloseResponse:
    user_id = int(payload["sub"])
    status, ended_at = await disaster_service.close_disaster(
        user_id=user_id,
        user_disaster_id=userDisasterId,
        action=req.action,
        ended_at=req.endedAt,
    )
    message = (
        "재난이 종료 처리되었습니다."
        if status == "EXPIRED"
        else "재난이 보관 처리되었습니다."
    )
    return DisasterCloseResponse(
        userDisasterId=userDisasterId,
        status=status,
        endedAt=ended_at,
        message=message,
    )


