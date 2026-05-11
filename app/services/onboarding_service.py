from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from app.schemas import onboarding as schemas
from app.crud import onboarding as crud

# 배열에서 안전하게 값을 가져오기 위한 헬퍼 함수
def safe_get(arr: list, index: int, default: bool = False) -> bool:
    return arr[index] if index < len(arr) else default

def process_onboarding(db: Session, req: schemas.OnboardingRequest) -> schemas.OnboardingResponse:
    # 1. 공통 피해 정보 저장
    impact = crud.create_disaster_impact(db, req)
    arr = req.damages

    # 2. 재난 타입별 배열 인덱스 매핑 및 저장
    if req.disaster_type == schemas.DisasterType.FLOOD:
        if not req.flood_level or not req.water_drain_status:
            raise HTTPException(status_code=400, detail="홍수 필수 필드 누락 (floodLevel, waterDrainStatus)")
            
        # 순서: [주거(0), 차량(1), 전기(2), 수도(3), 심리(4)]
        crud.create_flood_impact(db, {
            "impact_id": impact.impact_id,
            "flood_level": req.flood_level.value,
            "water_drain_status": req.water_drain_status.value,
            "damage_house": safe_get(arr, 0),
            "damage_vehicle": safe_get(arr, 1),
            "electric_problem": safe_get(arr, 2),
            "water_problem": safe_get(arr, 3)
        })

    elif req.disaster_type == schemas.DisasterType.TYPHOON:
        # 순서: [지붕(0), 창문(1), 간판/구조물(2), 차량(3), 전기(4), 수도(5), 부상(6), 심리(7)]
        crud.create_typhoon_impact(db, {
            "impact_id": impact.impact_id,
            "roof_damage": safe_get(arr, 0),
            "window_damage": safe_get(arr, 1),
            "structure_damage": safe_get(arr, 2),
            "vehicle_damage": safe_get(arr, 3),
            "electric_problem": safe_get(arr, 4),
            "water_problem": safe_get(arr, 5)
        })

    elif req.disaster_type == schemas.DisasterType.EARTHQUAKE:
        if not req.aftershock_feeling:
            raise HTTPException(status_code=400, detail="지진 필수 필드 누락 (aftershockFeeling)")
            
        # 순서: [균열(0), 주거(1), 차량(2), 전기(3), 수도(4), 부상(5), 심리(6)]
        crud.create_earthquake_impact(db, {
            "impact_id": impact.impact_id,
            "aftershock_feeling": req.aftershock_feeling.value,
            "building_crack": safe_get(arr, 0),
            "house_damage": safe_get(arr, 1),
            "vehicle_damage": safe_get(arr, 2),
            "electric_problem": safe_get(arr, 3),
            "water_problem": safe_get(arr, 4)
        })

    elif req.disaster_type == schemas.DisasterType.FIRE:
        if not req.fire_damage_scope or not req.smoke_inhalation:
            raise HTTPException(status_code=400, detail="화재 필수 필드 누락 (fireDamageScope, smokeInhalation)")
            
        # 순서: [주거(0), 차량(1), 전기(2), 수도(3), 부상(4), 심리(5), 그을음(6), 잔해(7)]
        crud.create_fire_impact(db, {
            "impact_id": impact.impact_id,
            "fire_damage_scope": req.fire_damage_scope.value,
            "smoke_inhalation": req.smoke_inhalation.value,
            "house_damage": safe_get(arr, 0),
            "vehicle_damage": safe_get(arr, 1),
            "electric_problem": safe_get(arr, 2),
            "water_problem": safe_get(arr, 3),
            "soot_damage": safe_get(arr, 6),
            "debris_exist": safe_get(arr, 7)
        })

    return schemas.OnboardingResponse(
        impact_id=impact.impact_id,
        message="피해 상황이 등록되었습니다"
    )