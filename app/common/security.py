"""JWT 발급·Firebase ID 토큰 검증 (네트워크 호출은 스레드로 오프로딩)."""

import asyncio
from datetime import datetime, timedelta, timezone

from jose import jwt

from app.config import settings


async def verify_firebase_id_token(id_token: str) -> dict:
    """Firebase Admin SDK로 ID 토큰 검증. 실패 시 Firebase 예외."""
    from firebase_admin import auth as firebase_auth

    return await asyncio.to_thread(firebase_auth.verify_id_token, id_token)


async def delete_firebase_user(uid: str) -> None:
    """Firebase Auth 사용자 삭제. 없으면 무시."""
    from firebase_admin import auth as firebase_auth

    def _delete() -> None:
        try:
            firebase_auth.delete_user(uid)
        except firebase_auth.UserNotFoundError:
            return

    await asyncio.to_thread(_delete)


def create_access_token(*, user_id: int, firebase_uid: str) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user_id),
        "firebase_uid": firebase_uid,
        "type": "access",
        "iat": now,
        "exp": now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
    }
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def create_refresh_token(*, user_id: int, jti: str, expires_at: datetime) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user_id),
        "type": "refresh",
        "jti": jti,
        "iat": now,
        "exp": expires_at,
    }
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_access_token_claims(token: str) -> dict:
    """액세스 JWT 검증 (만료·서명·alg)."""
    return jwt.decode(
        token,
        settings.JWT_SECRET_KEY,
        algorithms=[settings.JWT_ALGORITHM],
    )


def decode_refresh_token_claims(token: str) -> dict:
    """리프레시 JWT 검증 (만료·서명·alg)."""
    return jwt.decode(
        token,
        settings.JWT_SECRET_KEY,
        algorithms=[settings.JWT_ALGORITHM],
    )


def decode_refresh_token_for_logout(token: str) -> dict:
    """로그아웃 전용: 서명·alg는 검증하고 exp는 건너뜀."""
    return jwt.decode(
        token,
        settings.JWT_SECRET_KEY,
        algorithms=[settings.JWT_ALGORITHM],
        options={"verify_exp": False},
    )


__all__ = [
    "create_access_token",
    "create_refresh_token",
    "decode_access_token_claims",
    "decode_refresh_token_claims",
    "decode_refresh_token_for_logout",
    "delete_firebase_user",
    "verify_firebase_id_token",
]
