from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.base import get_db
from app.schemas import checklist as schemas
from app.crud import checklist as crud_checklist
from app.models import onboarding as onboard_models
from app.services import gemini_service

router = APIRouter(prefix="/api/v1/checklists", tags=["Checklist"])

@router.post("/ai-generate", response_model=schemas.ChecklistGenerateResponse)
def generate_ai_checklist(
    req: schemas.ChecklistGenerateRequest,
    db: Session = Depends(get_db)
):
    # DB에서 온보딩(DisasterImpact) 정보 가져오기
    impact = db.query(onboard_models.DisasterImpact).filter(
        onboard_models.DisasterImpact.user__disaster_id == req.user_disaster_id
    ).first()
    
    if not impact:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="해당 사용자의 재난 온보딩 정보가 존재하지 않습니다."
        )

    # Gemini 프롬프트 생성 
    prompt = gemini_service.build_disaster_prompt(db, impact)
    
    # Gemini API 호출하여 3개의 타이틀 받아오기
    generated_titles = gemini_service.generate_checklist_from_gemini(prompt)
    
    # DB에 체크리스트 저장
    db_items = crud_checklist.create_ai_checklists(
        db=db, 
        user_disaster_id=req.user_disaster_id, 
        target_date=req.target_date, 
        titles=generated_titles
    )
    
    response_items = [
        schemas.GeneratedItemInfo(
            checklist_item_id=item.checklist_item_id,
            title=item.title,
            item_source_type=item.item_source_type
        ) for item in db_items
    ]
    
    return schemas.ChecklistGenerateResponse(items=response_items)