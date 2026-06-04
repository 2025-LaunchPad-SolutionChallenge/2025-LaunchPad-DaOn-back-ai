from typing import Optional

from app.common.exceptions import BadRequestException, NotFoundException
from app.domain.disaster.entity import (
    DisasterImpact,
    EarthquakeDetail,
    FireDetail,
    FloodDetail,
    TyphoonDetail,
)
from app.domain.disaster.repository import DisasterRepository
from app.domain.recovery.service import calculate_onboarding_risk_level


def _safe_get(arr: list, index: int, default: bool = False) -> bool:
    return arr[index] if index < len(arr) else default


# 재난 유형별 damages 배열에서 심리적 불안 인덱스
_PSYCHOLOGICAL_INDEX = {
    "FLOOD": 4,
    "TYPHOON": 7,
    "EARTHQUAKE": 6,
    "FIRE": 5,
}


async def process_onboarding(
    repo: DisasterRepository,
    user_id: int,
    disaster_type: str,
    safety_status: Optional[str],
    residence_status: str,
    injury_level: str,
    damages: list[bool],
    flood_level: Optional[str] = None,
    water_drain_status: Optional[str] = None,
    aftershock_feeling: Optional[str] = None,
    fire_damage_scope: Optional[str] = None,
    smoke_inhalation: Optional[str] = None,
) -> DisasterImpact:
    disaster_type_id = await repo.get_disaster_type_id_by_code(disaster_type)
    initial_stage_id = await repo.get_initial_recovery_stage_id()
    user_disaster_id = await repo.create_user_disaster(user_id, disaster_type_id, initial_stage_id)

    psych_index = _PSYCHOLOGICAL_INDEX.get(disaster_type)
    psychological_anxiety = _safe_get(damages, psych_index) if psych_index is not None else False

    impact = DisasterImpact(
        user_disaster_id=user_disaster_id,
        safety_status=safety_status,
        residence_status=residence_status,
        injury_level=injury_level,
        psychological_anxiety=psychological_anxiety,
    )
    impact.onboarding_risk_level = calculate_onboarding_risk_level(impact)
    saved = await repo.create_impact(impact)

    if disaster_type == "FLOOD":
        if not flood_level or not water_drain_status:
            raise BadRequestException("홍수 필수 필드 누락 (floodLevel, waterDrainStatus)")
        await repo.create_flood_detail(
            FloodDetail(
                impact_id=saved.impact_id,
                flood_level=flood_level,
                water_drain_status=water_drain_status,
                damage_house=_safe_get(damages, 0),
                damage_vehicle=_safe_get(damages, 1),
                electric_problem=_safe_get(damages, 2),
                water_problem=_safe_get(damages, 3),
            )
        )
    elif disaster_type == "TYPHOON":
        await repo.create_typhoon_detail(
            TyphoonDetail(
                impact_id=saved.impact_id,
                roof_damage=_safe_get(damages, 0),
                window_damage=_safe_get(damages, 1),
                structure_damage=_safe_get(damages, 2),
                vehicle_damage=_safe_get(damages, 3),
                electric_problem=_safe_get(damages, 4),
                water_problem=_safe_get(damages, 5),
            )
        )
    elif disaster_type == "EARTHQUAKE":
        if not aftershock_feeling:
            raise BadRequestException("지진 필수 필드 누락 (aftershockFeeling)")
        await repo.create_earthquake_detail(
            EarthquakeDetail(
                impact_id=saved.impact_id,
                aftershock_feeling=aftershock_feeling,
                building_crack=_safe_get(damages, 0),
                house_damage=_safe_get(damages, 1),
                vehicle_damage=_safe_get(damages, 2),
                electric_problem=_safe_get(damages, 3),
                water_problem=_safe_get(damages, 4),
            )
        )
    elif disaster_type == "FIRE":
        if not fire_damage_scope or not smoke_inhalation:
            raise BadRequestException("화재 필수 필드 누락 (fireDamageScope, smokeInhalation)")
        await repo.create_fire_detail(
            FireDetail(
                impact_id=saved.impact_id,
                fire_damage_scope=fire_damage_scope,
                smoke_inhalation=smoke_inhalation,
                house_damage=_safe_get(damages, 0),
                vehicle_damage=_safe_get(damages, 1),
                electric_problem=_safe_get(damages, 2),
                water_problem=_safe_get(damages, 3),
                soot_damage=_safe_get(damages, 6),
                debris_exist=_safe_get(damages, 7),
            )
        )

    return saved


async def update_checklist_context(
    repo: DisasterRepository,
    user_disaster_id: int,
    can_go_out: bool,
    available_time: str,
) -> DisasterImpact:
    updated = await repo.update_context(user_disaster_id, can_go_out, available_time)
    if not updated:
        raise NotFoundException("해당 userDisasterId에 대한 온보딩 정보를 찾을 수 없습니다.")
    return updated
