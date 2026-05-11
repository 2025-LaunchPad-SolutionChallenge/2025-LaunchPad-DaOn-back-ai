from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.schemas import onboarding as schemas
from app.services import onboarding_service as services
from app.db.session import get_db

router = APIRouter(prefix="/api/v1/disasters", tags=["Onboarding"])

@router.post("/onboarding", response_model=schemas.OnboardingResponse)
def submit_onboarding(
    req: schemas.OnboardingRequest, 
    db: Session = Depends(get_db)
):
    """
    단일 엔드포인트 온보딩
    프론트엔드에서 disasterType과 damages(배열)를 포함하여 요청합니다.
    """
    return services.process_onboarding(db, req)