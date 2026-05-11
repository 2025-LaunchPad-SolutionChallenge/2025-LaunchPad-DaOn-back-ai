from sqlalchemy.orm import Session
from app.models import checklist as models
from typing import List
from datetime import date

def create_ai_checklists(db: Session, user_disaster_id: int, target_date: date, titles: List[str]) -> List[models.ChecklistItem]:
    created_items = []
    
    for title in titles:
        new_item = models.ChecklistItem(
            user__disaster_id=user_disaster_id,
            checklist_date=target_date,
            title=title,
            item_source_type="AI_GENERATED",
            priority=1,
            is_completed=False
        )
        db.add(new_item)
        created_items.append(new_item)
        
    db.commit()
    
    # 생성된 ID를 받아오기 위해 refresh 수행
    for item in created_items:
        db.refresh(item)
        
    return created_items