from datetime import datetime, timezone

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.auth.entity import ResidenceVerificationResult, StoredRefreshSession
from app.domain.auth.repository import AuthRepository
from app.infrastructure.models.refresh_token_session_model import RefreshTokenSessionModel
from app.infrastructure.models.residence_verification_model import (
    ResidenceVerificationLogModel,
    ResidenceVerificationModel,
)
from app.infrastructure.models.user_model import UserModel


def _utc_now_naive() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _to_stored(row: RefreshTokenSessionModel) -> StoredRefreshSession:
    return StoredRefreshSession(
        user_id=row.user_id,
        jti=row.jti,
        expires_at=row.expires_at,
        revoked_at=row.revoked_at,
    )


def _to_residence_result(row: ResidenceVerificationModel) -> ResidenceVerificationResult:
    return ResidenceVerificationResult(
        status="VERIFIED",
        verified=True,
        distance_km=float(row.last_distance_km),
        threshold_km=float(row.threshold_km),
        verification_count=row.verification_count,
        verified_at=row.verified_at,
        expires_at=row.expires_at,
        days_until_expiry=None,
        message=None,
    )


class SqlAlchemyAuthRepository(AuthRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def persist_refresh_token(
        self,
        user_id: int,
        jti: str,
        expires_at: datetime,
    ) -> None:
        exp = expires_at.replace(tzinfo=None) if expires_at.tzinfo else expires_at
        row = RefreshTokenSessionModel(
            user_id=user_id,
            jti=jti,
            expires_at=exp,
            revoked_at=None,
        )
        self._session.add(row)
        await self._session.flush()

    async def get_refresh_session(self, jti: str) -> StoredRefreshSession | None:
        result = await self._session.execute(
            select(RefreshTokenSessionModel).where(RefreshTokenSessionModel.jti == jti),
        )
        row = result.scalar_one_or_none()
        return _to_stored(row) if row else None

    async def revoke_refresh_session(self, jti: str) -> None:
        now = _utc_now_naive()
        await self._session.execute(
            update(RefreshTokenSessionModel)
            .where(
                RefreshTokenSessionModel.jti == jti,
                RefreshTokenSessionModel.revoked_at.is_(None),
            )
            .values(revoked_at=now),
        )
        await self._session.flush()

    async def revoke_all_refresh_sessions_by_user(self, user_id: int) -> None:
        now = _utc_now_naive()
        await self._session.execute(
            update(RefreshTokenSessionModel)
            .where(
                RefreshTokenSessionModel.user_id == user_id,
                RefreshTokenSessionModel.revoked_at.is_(None),
            )
            .values(revoked_at=now),
        )
        await self._session.flush()

    async def get_user_exists(self, user_id: int) -> bool:
        result = await self._session.execute(
            select(UserModel.user_id).where(UserModel.user_id == user_id),
        )
        return result.scalar_one_or_none() is not None

    async def get_last_verified_attempt_at(self, user_id: int) -> datetime | None:
        result = await self._session.execute(
            select(ResidenceVerificationLogModel.verified_at)
            .where(ResidenceVerificationLogModel.user_id == user_id)
            .order_by(ResidenceVerificationLogModel.verified_at.desc())
            .limit(1),
        )
        return result.scalar_one_or_none()

    async def get_residence_baseline(self, user_id: int) -> tuple[float, float] | None:
        result = await self._session.execute(
            select(
                ResidenceVerificationModel.disaster_latitude,
                ResidenceVerificationModel.disaster_longitude,
            ).where(ResidenceVerificationModel.user_id == user_id),
        )
        row = result.one_or_none()
        if row is None:
            return None
        return float(row[0]), float(row[1])

    async def log_residence_attempt(
        self,
        *,
        user_id: int,
        current_latitude: float,
        current_longitude: float,
        distance_km: float,
        is_success: bool,
        now: datetime,
    ) -> None:
        log = ResidenceVerificationLogModel(
            user_id=user_id,
            current_latitude=current_latitude,
            current_longitude=current_longitude,
            distance_km=distance_km,
            is_success=is_success,
            verified_at=now,
        )
        self._session.add(log)
        await self._session.flush()

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
    ) -> ResidenceVerificationResult:
        result = await self._session.execute(
            select(ResidenceVerificationModel).where(ResidenceVerificationModel.user_id == user_id),
        )
        row = result.scalar_one_or_none()

        if row is None:
            row = ResidenceVerificationModel(
                user_id=user_id,
                disaster_latitude=disaster_latitude,
                disaster_longitude=disaster_longitude,
                last_current_lat=current_latitude,
                last_current_lng=current_longitude,
                last_address=current_address,
                last_distance_km=distance_km,
                threshold_km=threshold_km,
                verification_count=1,
                verified_at=now,
                expires_at=expires_at,
            )
            self._session.add(row)
        else:
            row.last_current_lat = current_latitude
            row.last_current_lng = current_longitude
            row.last_address = current_address
            row.last_distance_km = distance_km
            row.threshold_km = threshold_km
            row.verification_count = int(row.verification_count) + 1
            row.verified_at = now
            row.expires_at = expires_at

        log = ResidenceVerificationLogModel(
            user_id=user_id,
            current_latitude=current_latitude,
            current_longitude=current_longitude,
            distance_km=distance_km,
            is_success=True,
            verified_at=now,
        )
        self._session.add(log)

        await self._session.flush()
        return _to_residence_result(row)

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
    ) -> ResidenceVerificationResult | None:
        result = await self._session.execute(
            select(ResidenceVerificationModel).where(ResidenceVerificationModel.user_id == user_id),
        )
        row = result.scalar_one_or_none()
        if row is None:
            return None

        row.last_current_lat = current_latitude
        row.last_current_lng = current_longitude
        row.last_address = current_address
        row.last_distance_km = distance_km
        row.threshold_km = threshold_km
        row.verification_count = int(row.verification_count) + 1
        row.verified_at = now
        row.expires_at = expires_at

        await self.log_residence_attempt(
            user_id=user_id,
            current_latitude=current_latitude,
            current_longitude=current_longitude,
            distance_km=distance_km,
            is_success=True,
            now=now,
        )

        await self._session.flush()
        return _to_residence_result(row)

    async def get_residence_verification(self, user_id: int) -> ResidenceVerificationResult | None:
        result = await self._session.execute(
            select(ResidenceVerificationModel).where(ResidenceVerificationModel.user_id == user_id),
        )
        row = result.scalar_one_or_none()
        if row is None:
            return None
        return _to_residence_result(row)
