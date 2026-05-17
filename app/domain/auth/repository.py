from abc import ABC, abstractmethod
from datetime import datetime

from app.domain.auth.entity import StoredRefreshSession


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
