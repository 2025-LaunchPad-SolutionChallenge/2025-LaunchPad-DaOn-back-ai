from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime

from app.domain.disaster.entity import DisasterDetail, DisasterListPage


class DisasterRepository(ABC):
    @abstractmethod
    async def get_disasters_page(self, *, user_id: int, page: int, size: int) -> DisasterListPage: ...

    @abstractmethod
    async def get_disaster_detail(self, *, user_id: int, user_disaster_id: int) -> DisasterDetail | None: ...

    @abstractmethod
    async def update_disaster(
        self,
        *,
        user_id: int,
        user_disaster_id: int,
        title: str | None = None,
        occurred_at: datetime | None = None,
        impact_updates: dict[str, object] | None = None,
        detail_updates: dict[str, object] | None = None,
    ) -> None: ...

    @abstractmethod
    async def close_disaster(
        self,
        *,
        user_id: int,
        user_disaster_id: int,
        action: str,
        ended_at: datetime | None,
    ) -> tuple[str, datetime]: ...
