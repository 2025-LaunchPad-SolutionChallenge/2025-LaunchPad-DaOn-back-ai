from abc import ABC, abstractmethod
from datetime import datetime

from app.domain.auth.entity import ResidenceVerificationResult, StoredRefreshSession


class AuthRepository(ABC):
    """리프레시 토큰 세션 영속화 (회전·로그아웃 무효화)."""

    @abstractmethod
    async def persist_refresh_token(
        self,
        user_id: int,
        jti: str,
        expires_at: datetime,
    ) -> None: ...

    @abstractmethod
    async def get_refresh_session(self, jti: str) -> StoredRefreshSession | None: ...

    @abstractmethod
    async def revoke_refresh_session(self, jti: str) -> None: ...

    @abstractmethod
    async def revoke_all_refresh_sessions_by_user(self, user_id: int) -> None: ...

    @abstractmethod
    async def get_user_exists(self, user_id: int) -> bool: ...

    @abstractmethod
    async def get_last_verified_attempt_at(self, user_id: int) -> datetime | None: ...

    @abstractmethod
    async def get_residence_baseline(self, user_id: int) -> tuple[float, float] | None: ...

    @abstractmethod
    async def log_residence_attempt(
        self,
        *,
        user_id: int,
        current_latitude: float,
        current_longitude: float,
        distance_km: float,
        is_success: bool,
        now: datetime,
    ) -> None: ...

    @abstractmethod
    async def verify_residence_first(
        self,
        *,
        user_id: int,
        disaster_latitude: float,
        disaster_longitude: float,
        current_latitude: float,
        current_longitude: float,
        current_address: str | None,
        distance_km: float,
        threshold_km: float,
        now: datetime,
        expires_at: datetime,
    ) -> ResidenceVerificationResult: ...

    @abstractmethod
    async def verify_residence_re(
        self,
        *,
        user_id: int,
        current_latitude: float,
        current_longitude: float,
        current_address: str | None,
        distance_km: float,
        threshold_km: float,
        now: datetime,
        expires_at: datetime,
    ) -> ResidenceVerificationResult | None: ...

    @abstractmethod
    async def get_residence_verification(self, user_id: int) -> ResidenceVerificationResult | None: ...
