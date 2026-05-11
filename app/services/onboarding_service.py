from sqlalchemy.orm import Session
from app.crud import onboarding as crud
from app.schemas.onboarding import OnboardingRequest


class OnboardingService:

    @staticmethod
    def create_onboarding(db: Session, req: OnboardingRequest):

        # 1. disaster 존재 확인
        disaster = crud.get_disaster(db, req.disasterId)
        if not disaster:
            return None, "DISASTER_NOT_FOUND"

        # 2. 재난 타입 자동 판별 (예: floodDetail 기준)
        detail_type = None
        detail_data = None

        if req.floodDetail:
            detail_type = "flood"
            detail_data = req.floodDetail.model_dump()
        else:
            return None, "INVALID_DISASTER_TYPE"

        # 3. 저장용 dict 구성
        payload = {
            "disaster_id": req.disasterId,
            "safety_status": req.safetyStatus,
            "residence_status": req.residenceStatus,
            "injury_level": req.injuryLevel,
            "detail_type": detail_type,
            "detail_data": detail_data,
        }

        impact = crud.create_impact(db, payload)

        return impact, None