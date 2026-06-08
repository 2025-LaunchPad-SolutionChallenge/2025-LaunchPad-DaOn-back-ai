from abc import ABC, abstractmethod
from typing import Optional

from app.domain.disaster.entity import (
    DisasterImpact,
    DisasterImpactFull,
    EarthquakeDetail,
    FireDetail,
    FloodDetail,
    TyphoonDetail,
)


class DisasterRepository(ABC):
    @abstractmethod
    async def get_disaster_type_id_by_code(self, code: str) -> int: ...

    @abstractmethod
    async def get_initial_recovery_stage_id(self) -> int: ...

    @abstractmethod
    async def create_user_disaster(
        self, user_id: int, disaster_type_id: int, recovery_stage_id: int
    ) -> int: ...

    @abstractmethod
    async def upsert_user_setting(self, user_id: int, user_disaster_id: int) -> None: ...

    @abstractmethod
    async def create_impact(self, impact: DisasterImpact) -> DisasterImpact: ...

    @abstractmethod
    async def create_flood_detail(self, detail: FloodDetail) -> None: ...

    @abstractmethod
    async def create_typhoon_detail(self, detail: TyphoonDetail) -> None: ...

    @abstractmethod
    async def create_earthquake_detail(self, detail: EarthquakeDetail) -> None: ...

    @abstractmethod
    async def create_fire_detail(self, detail: FireDetail) -> None: ...

    @abstractmethod
    async def update_context(
        self, user_disaster_id: int, can_go_out: bool, available_time: str
    ) -> Optional[DisasterImpact]: ...

    @abstractmethod
    async def get_impact_full(
        self, user_disaster_id: int
    ) -> Optional[DisasterImpactFull]: ...
