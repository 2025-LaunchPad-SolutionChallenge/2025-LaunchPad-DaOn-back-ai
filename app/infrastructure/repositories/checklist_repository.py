from typing import List

from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.checklist.entity import ChecklistItem
from app.domain.checklist.repository import ChecklistRepository
from app.infrastructure.models.checklist_model import ChecklistItemModel


def _model_to_entity(model: ChecklistItemModel) -> ChecklistItem:
    return ChecklistItem(
        checklist_item_id=model.checklist_item_id,
        user_disaster_id=model.user_disaster_id,
        checklist_date=model.checklist_date,
        title=model.title,
        memo=model.memo,
        item_source_type=model.item_source_type,
        priority=model.priority,
        is_completed=model.is_completed,
        completed_at=model.completed_at,
    )


class SQLChecklistRepository(ChecklistRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def save_items(self, items: List[ChecklistItem]) -> List[ChecklistItem]:
        models = [
            ChecklistItemModel(
                user_disaster_id=item.user_disaster_id,
                checklist_date=item.checklist_date,
                title=item.title,
                memo=item.memo,
                item_source_type=item.item_source_type,
                priority=item.priority,
                is_completed=item.is_completed,
            )
            for item in items
        ]
        self._session.add_all(models)
        await self._session.flush()
        for model in models:
            await self._session.refresh(model)
        return [_model_to_entity(m) for m in models]
