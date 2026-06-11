from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import date, datetime

from app.domain.checklist.entity import ChecklistItem


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

    @abstractmethod
    async def patch_checklist_status(
        self,
        *,
        user_id: int,
        user_disaster_id: int,
        checklist_item_id: int,
        completed: bool,
    ) -> tuple[int, bool, datetime | None]: ...

    @abstractmethod
    async def delete_checklist_item(
        self,
        *,
        user_id: int,
        user_disaster_id: int,
        checklist_item_id: int,
    ) -> tuple[int, int]: ...

    @abstractmethod
    async def get_checklist_detail(
        self,
        *,
        user_id: int,
        user_disaster_id: int,
        checklist_item_id: int,
    ) -> tuple[dict[str, object], list[dict[str, object]]]: ...

    @abstractmethod
    async def get_checklists_by_date_range(
        self,
        *,
        user_id: int,
        user_disaster_id: int,
        start_date: date,
        end_date: date,
    ) -> list[dict[str, object]]: ...

    @abstractmethod
    async def get_archives(
        self,
        *,
        user_id: int,
        user_disaster_id: int,
        archive_type: str,
        date_value: date | None,
        cursor: str | None,
        limit: int,
    ) -> tuple[list[dict[str, object]], str | None, bool]: ...

    @abstractmethod
    async def save_items(self, items: list[ChecklistItem]) -> list[ChecklistItem]: ...

    @abstractmethod
    async def get_impact_full(self, *, user_id: int, user_disaster_id: int) -> dict[str, object] | None: ...

    @abstractmethod
    async def update_context(
        self,
        *,
        user_id: int,
        user_disaster_id: int,
        can_go_out: bool,
        available_time: str,
    ) -> None: ...

    @abstractmethod
    async def get_weekly_completion_stats(
        self,
        *,
        user_id: int,
        user_disaster_id: int,
        week_start_date: date,
        week_end_date: date,
    ) -> tuple[int, int]: ...
