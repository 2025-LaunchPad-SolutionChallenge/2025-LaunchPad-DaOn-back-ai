from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Optional


@dataclass
class ChecklistItem:
    user_disaster_id: int
    checklist_date: date
    title: str
    item_source_type: str
    checklist_item_id: Optional[int] = None
    memo: Optional[str] = None
    priority: int = 1
    is_completed: bool = False
    completed_at: Optional[datetime] = None
