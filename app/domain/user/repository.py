from abc import ABC, abstractmethod
from datetime import date

from app.domain.user.entity import User


class UserRepository(ABC):
    """유저 영속화 포트. 인프라에서 구현."""

    @abstractmethod
    async def get_by_id(self, user_id: int) -> User | None: ...

    @abstractmethod
    async def get_by_firebase_uid(self, firebase_uid: str) -> User | None: ...

    @abstractmethod
    async def create(
        self,
        *,
        firebase_uid: str,
        name: str | None,
        birth_date: date | None,
        email: str | None,
        profile_image_url: str | None,
    ) -> User: ...

    @abstractmethod
    async def delete(self, user_id: int) -> None: ...

    @abstractmethod
    async def ensure_google_provider(
        self,
        user_id: int,
        provider_uid: str,
        provider_email: str | None,
        email_verified: bool,
    ) -> None: ...
