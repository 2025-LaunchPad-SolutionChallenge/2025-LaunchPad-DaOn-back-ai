from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.dependencies import get_db
from app.common.security import get_current_user
from app.domain.checklist import service as checklist_service
from app.infrastructure.repositories.checklist_repository import SQLChecklistRepository
from app.infrastructure.repositories.disaster_repository import SQLDisasterRepository
from app.interface.checklist.schema import (
    ChecklistGenerateRequest,
    ChecklistGenerateResponse,
    GeneratedItemInfo,
)

router = APIRouter(prefix="/checklists", tags=["checklists"])


@router.post("/ai-generate", response_model=ChecklistGenerateResponse)
async def generate_ai_checklist(
    req: ChecklistGenerateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: dict[str, Any] = Depends(get_current_user),
) -> ChecklistGenerateResponse:
    disaster_repo = SQLDisasterRepository(db)
    impact_full = await disaster_repo.get_impact_full(req.user_disaster_id)

    checklist_repo = SQLChecklistRepository(db)
    items = await checklist_service.generate_ai_checklist(
        repo=checklist_repo,
        impact_full=impact_full,
        user_disaster_id=req.user_disaster_id,
        target_date=req.target_date,
    )

    return ChecklistGenerateResponse(
        items=[
            GeneratedItemInfo(
                checklist_item_id=item.checklist_item_id,
                title=item.title,
                item_source_type=item.item_source_type,
            )
            for item in items
        ]
    )
