from datetime import datetime, timezone

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.auth.entity import StoredRefreshSession
from app.domain.auth.repository import AuthRepository
from app.infrastructure.models.refresh_token_session_model import RefreshTokenSessionModel


def _utc_now_naive() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _to_stored(row: RefreshTokenSessionModel) -> StoredRefreshSession:
    return StoredRefreshSession(
        user_id=row.user_id,
        jti=row.jti,
        expires_at=row.expires_at,
        revoked_at=row.revoked_at,
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
