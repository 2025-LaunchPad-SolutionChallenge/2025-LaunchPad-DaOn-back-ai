from abc import ABC, abstractmethod
from typing import List

from app.domain.checklist.entity import ChecklistItem


class ChecklistRepository(ABC):
    @abstractmethod
    async def save_items(self, items: List[ChecklistItem]) -> List[ChecklistItem]: ...
