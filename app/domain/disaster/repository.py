from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import date, datetime

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

    @abstractmethod
    async def create_onboarding(
        self,
        *,
        user_id: int,
        disaster_type: str,
        latitude: float | None,
        longitude: float | None,
        address: str | None,
        safety_status: str | None,
        residence_status: str,
        injury_level: str,
        damages: list[bool],
        flood_level: str | None,
        water_drain_status: str | None,
        aftershock_feeling: str | None,
        fire_damage_scope: str | None,
        smoke_inhalation: str | None,
    ) -> tuple[int, int, int]: ...

    @abstractmethod
    async def get_recovery_stage_detail(
        self,
        *,
        user_id: int,
        user_disaster_id: int,
    ) -> tuple[int, str, str, str]: ...

    @abstractmethod
    async def get_recovery_graph_points(
        self,
        *,
        user_id: int,
        user_disaster_id: int,
    ) -> list[tuple[date, float | None, str, str]]: ...

    @abstractmethod
    async def get_latest_recovery_progress(
        self,
        *,
        user_id: int,
        user_disaster_id: int,
    ) -> tuple[float, str, str, str]: ...
