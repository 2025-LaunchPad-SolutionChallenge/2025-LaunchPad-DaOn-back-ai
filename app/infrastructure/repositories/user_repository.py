from datetime import date

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.user.entity import User
from app.domain.user.repository import UserRepository
from app.infrastructure.models.user_model import ProviderType, UserAuthProviderModel, UserModel


def _to_domain(model: UserModel) -> User:
    return User(
        id=model.user_id,
        firebase_uid=model.firebase_uid,
        name=model.name,
        nickname=model.nickname,
        profile_image_url=model.profile_image_url,
        birth_date=model.birth_date,
    )


class SqlAlchemyUserRepository(UserRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, user_id: int) -> User | None:
        result = await self._session.execute(select(UserModel).where(UserModel.user_id == user_id))
        row = result.scalar_one_or_none()
        return _to_domain(row) if row else None

    async def get_by_firebase_uid(self, firebase_uid: str) -> User | None:
        result = await self._session.execute(
            select(UserModel).where(UserModel.firebase_uid == firebase_uid),
        )
        row = result.scalar_one_or_none()
        return _to_domain(row) if row else None

    async def create(self, *, firebase_uid: str, name: str, birth_date: date) -> User:
        model = UserModel(
            firebase_uid=firebase_uid,
            name=name,
            birth_date=birth_date,
        )
        self._session.add(model)
        await self._session.flush()
        return _to_domain(model)

    async def delete(self, user_id: int) -> None:
        await self._session.execute(delete(UserModel).where(UserModel.user_id == user_id))
        await self._session.flush()

    async def ensure_google_provider(
        self,
        user_id: int,
        provider_uid: str,
        provider_email: str | None,
        email_verified: bool,
    ) -> None:
        result = await self._session.execute(
            select(UserAuthProviderModel).where(
                UserAuthProviderModel.user_id == user_id,
                UserAuthProviderModel.provider_type == ProviderType.GOOGLE,
            ),
        )
        if result.scalar_one_or_none() is not None:
            return
        row = UserAuthProviderModel(
            user_id=user_id,
            provider_type=ProviderType.GOOGLE,
            provider_uid=provider_uid,
            provider_email=provider_email,
            is_verified=email_verified,
        )
        self._session.add(row)
        await self._session.flush()
