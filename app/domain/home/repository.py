from abc import ABC, abstractmethod
from datetime import date
from typing import Optional

from app.domain.home.entity import DailyStatusCheck


class HomeRepository(ABC):
    @abstractmethod
    async def get_user_disaster_id(self, firebase_uid: str) -> Optional[int]: ...

    @abstractmethod
    async def exists_today(self, user_disaster_id: int, check_date: date) -> bool: ...

    @abstractmethod
    async def save_daily_check(self, check: DailyStatusCheck) -> DailyStatusCheck: ...

    @abstractmethod
    async def update_recovery_progress(
        self, user_disaster_id: int, total_score: int
    ) -> None: ...
