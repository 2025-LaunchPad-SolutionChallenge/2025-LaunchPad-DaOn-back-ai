from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import date


class ChecklistRepository(ABC):
    @abstractmethod
    async def add_checklist_item(
        self,
        *,
        user_id: int,
        user_disaster_id: int,
        title: str,
        checklist_date: date,
        priority: int,
    ) -> int: ...

    @abstractmethod
    async def patch_checklist_item(
        self,
        *,
        user_id: int,
        user_disaster_id: int,
        checklist_item_id: int,
        title: str | None,
        checklist_date: date | None,
        is_completed: bool | None,
        priority: int | None,
    ) -> int: ...

    @abstractmethod
    async def add_attachment(
        self,
        *,
        user_id: int,
        user_disaster_id: int,
        checklist_item_id: int,
        attachment_type: str,
        content: str | None,
        file_url: str | None,
        original_file_name: str | None,
        mime_type: str | None,
        file_size: int | None,
        thumbnail_url: str | None,
    ) -> int: ...

    @abstractmethod
    async def patch_attachment(
        self,
        *,
        user_id: int,
        user_disaster_id: int,
        checklist_item_id: int,
        attachment_id: int,
        content: str | None,
        file_url: str | None,
        original_file_name: str | None,
        mime_type: str | None,
        file_size: int | None,
        thumbnail_url: str | None,
    ) -> int: ...

    @abstractmethod
    async def delete_attachment(
        self,
        *,
        user_id: int,
        user_disaster_id: int,
        checklist_item_id: int,
        attachment_id: int,
    ) -> int: ...
