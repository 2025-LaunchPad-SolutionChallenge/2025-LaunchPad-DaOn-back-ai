from datetime import date, datetime

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.user.entity import User, UserProfile
from app.domain.user.repository import UserRepository
from app.infrastructure.models.checklist_model import ArchiveItemModel
from app.infrastructure.models.community_model import CommunityPostModel
from app.infrastructure.models.user_model import UserSettingModel
from app.infrastructure.models.user_model import (
    ProviderType,
    UserAuthProviderModel,
    UserModel,
    UserResidenceModel,
    VerificationStatus,
)


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

    async def create(
        self,
        *,
        firebase_uid: str,
        name: str | None,
        birth_date: date | None,
        email: str | None,
        profile_image_url: str | None,
    ) -> User:
        model = UserModel(
            firebase_uid=firebase_uid,
            name=name,
            email=email,
            birth_date=birth_date,
            profile_image_url=profile_image_url,
        )
        self._session.add(model)
        await self._session.flush()
        return _to_domain(model)

    async def delete(self, user_id: int) -> None:
        # 탈퇴 시 FK 제약을 만족하도록 수동 참조부터 정리한다.
        # archive_items.user_setting_id -> user_settings.user_setting_id (NO ACTION)
        await self._session.execute(
            delete(ArchiveItemModel).where(
                ArchiveItemModel.user_setting_id.in_(
                    select(UserSettingModel.user_setting_id).where(UserSettingModel.user_id == user_id)
                )
            )
        )
        # user_settings.user__disaster_id -> user_disasters.user__disaster_id (NO ACTION)
        await self._session.execute(delete(UserSettingModel).where(UserSettingModel.user_id == user_id))
        # community_posts.user_id / user__disaster_id / residence_id FK도 선제 정리
        await self._session.execute(delete(CommunityPostModel).where(CommunityPostModel.user_id == user_id))
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

    async def get_profile_by_user_id(self, user_id: int) -> UserProfile | None:
        user_result = await self._session.execute(
            select(UserModel).where(UserModel.user_id == user_id),
        )
        user_row = user_result.scalar_one_or_none()
        if user_row is None:
            return None

        residence_result = await self._session.execute(
            select(UserResidenceModel)
            .where(UserResidenceModel.user_id == user_id)
            .order_by(UserResidenceModel.created_at.desc(), UserResidenceModel.residence_id.desc()),
        )
        residence_row = residence_result.scalars().first()

        age = None
        if user_row.birth_date is not None:
            today = date.today()
            age = (
                today.year
                - user_row.birth_date.year
                - ((today.month, today.day) < (user_row.birth_date.month, user_row.birth_date.day))
            )

        residence_verified = bool(user_row.residence_verified)
        address_name = residence_row.address_name if residence_row is not None else None

        return UserProfile(
            user_id=user_row.user_id,
            name=user_row.name,
            nickname=user_row.nickname,
            birth_date=user_row.birth_date,
            age=age,
            profile_image_url=user_row.profile_image_url,
            residence_verified=residence_verified,
            address_name=address_name,
        )

    async def update_profile(
        self,
        *,
        user_id: int,
        nickname: str | None = None,
        address_name: str | None = None,
        profile_image_url: str | None = None,
    ) -> None:
        user_result = await self._session.execute(
            select(UserModel).where(UserModel.user_id == user_id),
        )
        user_row = user_result.scalar_one_or_none()
        if user_row is None:
            return

        if nickname is not None:
            user_row.nickname = nickname
        if profile_image_url is not None:
            user_row.profile_image_url = profile_image_url

        if address_name is not None:
            residence_result = await self._session.execute(
                select(UserResidenceModel)
                .where(UserResidenceModel.user_id == user_id)
                .order_by(UserResidenceModel.created_at.desc(), UserResidenceModel.residence_id.desc()),
            )
            residence_row = residence_result.scalars().first()
            now = datetime.utcnow()
            if residence_row is None:
                residence_row = UserResidenceModel(
                    user_id=user_id,
                    address_name=address_name,
                    verification_status=VerificationStatus.PENDING,
                    verified_at=None,
                    expires_at=None,
                )
                self._session.add(residence_row)
            else:
                residence_row.address_name = address_name

            user_row.residence_verified = False
            residence_row.verification_status = VerificationStatus.PENDING
            residence_row.verified_at = None
            residence_row.expires_at = now

        await self._session.flush()
