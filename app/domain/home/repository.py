from abc import ABC, abstractmethod
from datetime import date
from typing import Optional

from app.domain.home.entity import DailyStatusCheck, HomeSummary, TodayTask


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

    @abstractmethod
    async def get_active_user_disaster_id(self, user_id: int) -> Optional[int]: ...

    @abstractmethod
    async def get_home_summary(self, user_id: int) -> Optional[HomeSummary]: ...

    @abstractmethod
    async def get_today_tasks(
        self,
        *,
        user_disaster_id: int,
        today: date,
        limit: Optional[int] = None,
    ) -> list[TodayTask]: ...

    @abstractmethod
    async def get_today_status(self, user_disaster_id: int, today: date) -> Optional[DailyStatusCheck]: ...
