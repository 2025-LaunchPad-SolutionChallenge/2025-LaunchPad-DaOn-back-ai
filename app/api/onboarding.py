from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.schemas import onboarding as schemas
from app.services import onboarding_service as services
from app.db.session import get_db

router = APIRouter(prefix="/api/v1", tags=["Checklist & Onboarding"])

# 온보딩
@router.post("/onboarding", response_model=schemas.OnboardingResponse)
def submit_onboarding(
    req: schemas.OnboardingRequest, 
    db: Session = Depends(get_db)
):
    return services.process_onboarding(db, req)

# 상황 입력
@router.post("/checklists/context", response_model=schemas.ContextResponse)
def submit_checklist_context(
    req: schemas.ContextRequest, 
    db: Session = Depends(get_db)
):
    return services.process_checklist_context(db, req)