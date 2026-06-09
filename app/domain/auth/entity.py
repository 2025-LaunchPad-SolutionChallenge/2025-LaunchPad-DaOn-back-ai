from dataclasses import dataclass
from datetime import datetime

from app.domain.user.entity import User


@dataclass(frozen=True)
class StoredRefreshSession:
    """DB에 저장된 리프레시 토큰 세션(jti)."""

    user_id: int
    jti: str
    expires_at: datetime
    revoked_at: datetime | None


@dataclass(frozen=True)
class AuthTokensBundle:
    """Firebase 인증 후 발급되는 액세스·리프레시 토큰 묶음."""

    user: User
    access_token: str
    refresh_token: str
    is_new_user: bool


@dataclass(frozen=True)
class ResidenceVerificationResult:
    status: str
    verified: bool
    distance_km: float | None
    threshold_km: float | None
    verification_count: int | None
    verified_at: datetime | None
    expires_at: datetime | None
    days_until_expiry: int | None
    message: str | None
