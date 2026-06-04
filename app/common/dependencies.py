from collections.abc import AsyncGenerator

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose.exceptions import ExpiredSignatureError, JWTError
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.exceptions import AppException
from app.common.security import decode_access_token_claims
from app.database import AsyncSessionLocal
from app.domain.auth.service import AuthService
from app.infrastructure.repositories.auth_repository import SqlAlchemyAuthRepository
from app.infrastructure.repositories.user_repository import SqlAlchemyUserRepository

_bearer_optional = HTTPBearer(
    auto_error=False,
    scheme_name="BearerAuth",
    description="JWT 액세스 토큰",
)


async def get_current_access_payload(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer_optional),
) -> dict:
    if credentials is None:
        raise AppException(
            status_code=401,
            code=401,
            message="Authorization 헤더가 없거나 액세스 토큰이 유효하지 않습니다.",
            error_key="UNAUTHORIZED",
        )
    try:
        payload = decode_access_token_claims(credentials.credentials)
    except ExpiredSignatureError:
        raise AppException(
            status_code=401,
            code=401,
            message="액세스 토큰이 유효하지 않거나 만료되었습니다.",
            error_key="UNAUTHORIZED",
        )
    except JWTError:
        raise AppException(
            status_code=401,
            code=401,
            message="액세스 토큰이 유효하지 않습니다.",
            error_key="UNAUTHORIZED",
        )
    if payload.get("type") != "access":
        raise AppException(
            status_code=401,
            code=401,
            message="액세스 토큰이 유효하지 않습니다.",
            error_key="UNAUTHORIZED",
        )
    return payload


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def get_auth_service(db: AsyncSession = Depends(get_db)) -> AuthService:
    return AuthService(
        SqlAlchemyUserRepository(db),
        SqlAlchemyAuthRepository(db),
    )
