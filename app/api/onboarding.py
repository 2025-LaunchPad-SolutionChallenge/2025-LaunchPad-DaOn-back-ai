from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.schemas.onboarding import OnboardingRequest, OnboardingResponse
from app.services.onboarding_service import OnboardingService
from app.db.session import get_db

router = APIRouter(prefix="/api/v1/disasters", tags=["Onboarding"])


@router.post("/onboarding", response_model=OnboardingResponse)
def onboarding(req: OnboardingRequest, db: Session = Depends(get_db)):

    impact, error = OnboardingService.create_onboarding(db, req)

    if error == "DISASTER_NOT_FOUND":
        raise HTTPException(status_code=404, detail="DISASTER_NOT_FOUND")

    if error == "INVALID_DISASTER_TYPE":
        raise HTTPException(status_code=400, detail="INVALID_DISASTER_TYPE")

    return OnboardingResponse(
        impactId=impact.id,
        message="피해 상황이 등록되었습니다"
    )