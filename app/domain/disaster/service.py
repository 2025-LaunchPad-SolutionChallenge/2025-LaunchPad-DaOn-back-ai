from __future__ import annotations

from datetime import date, datetime

from app.common.exceptions import AppException
from app.domain.disaster.entity import DisasterDetail, DisasterListPage
from app.domain.disaster.repository import DisasterRepository


class DisasterService:
    def __init__(self, disaster_repo: DisasterRepository) -> None:
        self._disasters = disaster_repo

    async def get_disasters(self, *, user_id: int, page: int, size: int) -> DisasterListPage:
        return await self._disasters.get_disasters_page(user_id=user_id, page=page, size=size)

    async def get_disaster_detail(self, *, user_id: int, user_disaster_id: int) -> DisasterDetail:
        detail = await self._disasters.get_disaster_detail(
            user_id=user_id,
            user_disaster_id=user_disaster_id,
        )
        if detail is None:
            raise AppException(
                status_code=404,
                code=404,
                message="존재하지 않는 재난입니다.",
                error_key="DISASTER_NOT_FOUND",
            )
        return detail

    async def update_disaster(
        self,
        *,
        user_id: int,
        user_disaster_id: int,
        title: str | None,
        occurred_at: datetime | None,
        impact_updates: dict[str, object] | None,
        detail_updates: dict[str, object] | None,
    ) -> None:
        await self._disasters.update_disaster(
            user_id=user_id,
            user_disaster_id=user_disaster_id,
            title=title,
            occurred_at=occurred_at,
            impact_updates=impact_updates,
            detail_updates=detail_updates,
        )

    async def close_disaster(
        self,
        *,
        user_id: int,
        user_disaster_id: int,
        action: str,
        ended_at: datetime | None,
    ) -> tuple[str, datetime]:
        normalized = action.upper().strip()
        if normalized not in {"CLOSE", "ARCHIVE"}:
            raise AppException(
                status_code=400,
                code=400,
                message="action은 CLOSE 또는 ARCHIVE만 허용됩니다.",
                error_key="INVALID_ACTION",
            )
        return await self._disasters.close_disaster(
            user_id=user_id,
            user_disaster_id=user_disaster_id,
            action=normalized,
            ended_at=ended_at,
        )

    async def submit_onboarding(
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
    ) -> tuple[int, int, int]:
        if not damages:
            raise AppException(
                status_code=400,
                code=400,
                message="damages는 최소 1개 이상이어야 합니다.",
                error_key="MISSING_REQUIRED_FIELD",
            )
        return await self._disasters.create_onboarding(
            user_id=user_id,
            disaster_type=disaster_type,
            latitude=latitude,
            longitude=longitude,
            address=address,
            safety_status=safety_status,
            residence_status=residence_status,
            injury_level=injury_level,
            damages=damages,
            flood_level=flood_level,
            water_drain_status=water_drain_status,
            aftershock_feeling=aftershock_feeling,
            fire_damage_scope=fire_damage_scope,
            smoke_inhalation=smoke_inhalation,
        )

    async def get_recovery_stage_detail(
        self,
        *,
        user_id: int,
        user_disaster_id: int,
    ) -> tuple[int, str, str, str]:
        return await self._disasters.get_recovery_stage_detail(
            user_id=user_id,
            user_disaster_id=user_disaster_id,
        )

    async def get_recovery_graph_points(
        self,
        *,
        user_id: int,
        user_disaster_id: int,
    ) -> list[tuple[date, str, str]]:
        return await self._disasters.get_recovery_graph_points(
            user_id=user_id,
            user_disaster_id=user_disaster_id,
        )
