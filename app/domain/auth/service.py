import uuid
from datetime import date, datetime, timedelta, timezone
from math import asin, cos, radians, sin, sqrt

from firebase_admin.exceptions import FirebaseError
from jose.exceptions import ExpiredSignatureError, JWTError
from sqlalchemy.exc import IntegrityError

from app.common.exceptions import AppException
from app.common.security import (
    create_access_token,
    create_refresh_token,
    decode_refresh_token_claims,
    decode_refresh_token_for_logout,
    delete_firebase_user,
    verify_firebase_id_token,
)
from app.config import settings
from app.domain.auth.entity import AuthTokensBundle, ResidenceVerificationResult
from app.domain.auth.repository import AuthRepository
from app.domain.user.entity import User
from app.domain.user.repository import UserRepository


class AuthService:
    def __init__(self, user_repo: UserRepository, auth_repo: AuthRepository) -> None:
        self._users = user_repo
        self._auth = auth_repo

    async def _issue_session_tokens(self, user: User) -> tuple[str, str]:
        jti = str(uuid.uuid4())
        expires_at = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        access = create_access_token(user_id=user.id, firebase_uid=user.firebase_uid)
        refresh = create_refresh_token(user_id=user.id, jti=jti, expires_at=expires_at)
        await self._auth.persist_refresh_token(user.id, jti, expires_at)
        return access, refresh

    @staticmethod
    def _validate_coordinate(latitude: float, longitude: float) -> None:
        if latitude < -90 or latitude > 90 or longitude < -180 or longitude > 180:
            raise AppException(
                status_code=400,
                code=400,
                message="위경도 범위가 올바르지 않습니다.",
                error_key="INVALID_COORDINATE",
            )

    @staticmethod
    def _haversine_km(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
        rlat1 = radians(lat1)
        rlng1 = radians(lng1)
        rlat2 = radians(lat2)
        rlng2 = radians(lng2)
        dlat = rlat2 - rlat1
        dlng = rlng2 - rlng1
        a = sin(dlat / 2) ** 2 + cos(rlat1) * cos(rlat2) * sin(dlng / 2) ** 2
        c = 2 * asin(sqrt(a))
        return 6371.0 * c

    @staticmethod
    def _utc_now_naive() -> datetime:
        return datetime.now(timezone.utc).replace(tzinfo=None)

    async def _check_verify_cooldown(self, user_id: int, now: datetime) -> None:
        last_attempt = await self._auth.get_last_verified_attempt_at(user_id)
        if last_attempt is None:
            return
        cooldown_seconds = settings.RESIDENCE_VERIFY_COOLDOWN_MIN * 60
        elapsed = (now - last_attempt).total_seconds()
        if elapsed >= cooldown_seconds:
            return

        retry_after = int(cooldown_seconds - elapsed)
        if retry_after < 1:
            retry_after = 1
        raise AppException(
            status_code=429,
            code=429,
            message=f"{settings.RESIDENCE_VERIFY_COOLDOWN_MIN}분 내 재시도할 수 없습니다.",
            error_key="VERIFY_COOLDOWN",
            headers={"Retry-After": str(retry_after)},
        )

    @staticmethod
    def _format_status_response(
        row: ResidenceVerificationResult | None,
        *,
        now: datetime,
    ) -> ResidenceVerificationResult:
        if row is None:
            return ResidenceVerificationResult(
                status="NONE",
                verified=False,
                distance_km=None,
                threshold_km=None,
                verification_count=None,
                verified_at=None,
                expires_at=None,
                days_until_expiry=None,
                message="거주지 인증 내역이 없습니다.",
            )

        if row.expires_at is not None and row.expires_at < now:
            return ResidenceVerificationResult(
                status="EXPIRED",
                verified=False,
                distance_km=row.distance_km,
                threshold_km=row.threshold_km,
                verification_count=row.verification_count,
                verified_at=row.verified_at,
                expires_at=row.expires_at,
                days_until_expiry=0,
                message="거주지 인증이 만료되었습니다. 재인증이 필요합니다.",
            )

        days_left = None
        if row.expires_at is not None:
            delta = row.expires_at - now
            days_left = max(0, int(delta.total_seconds() // 86400))

        return ResidenceVerificationResult(
            status="VERIFIED",
            verified=True,
            distance_km=row.distance_km,
            threshold_km=row.threshold_km,
            verification_count=row.verification_count,
            verified_at=row.verified_at,
            expires_at=row.expires_at,
            days_until_expiry=days_left,
            message=None,
        )

    async def register(
        self,
        *,
        firebase_token: str,
        name: str | None,
        birth_date: date | None,
    ) -> AuthTokensBundle:
        try:
            decoded = await verify_firebase_id_token(firebase_token)
        except FirebaseError:
            raise AppException(
                status_code=401,
                code=401,
                message="Firebase ID 토큰이 유효하지 않거나 만료되었습니다.",
                error_key="INVALID_FIREBASE_TOKEN",
            )

        firebase_uid = decoded["uid"]
        resolved_name = (name or decoded.get("name") or decoded.get("display_name") or None)
        if isinstance(resolved_name, str):
            resolved_name = resolved_name.strip() or None
        else:
            resolved_name = None
        resolved_email = decoded.get("email")
        resolved_profile_image = decoded.get("picture")

        existing = await self._users.get_by_firebase_uid(firebase_uid)
        if existing is not None:
            raise AppException(
                status_code=409,
                code=409,
                message="이미 가입된 Firebase UID입니다.",
                error_key="DUPLICATE_FIREBASE_USER",
            )

        try:
            user = await self._users.create(
                firebase_uid=firebase_uid,
                name=resolved_name,
                birth_date=birth_date,
                email=resolved_email,
                profile_image_url=resolved_profile_image,
            )
        except IntegrityError:
            raise AppException(
                status_code=409,
                code=409,
                message="이미 가입된 Firebase UID입니다.",
                error_key="DUPLICATE_FIREBASE_USER",
            )

        await self._users.ensure_google_provider(
            user.id,
            firebase_uid,
            decoded.get("email"),
            bool(decoded.get("email_verified", False)),
        )

        access, refresh = await self._issue_session_tokens(user)

        return AuthTokensBundle(
            user=user,
            access_token=access,
            refresh_token=refresh,
            is_new_user=True,
        )

    async def login(self, *, firebase_token: str) -> AuthTokensBundle:
        try:
            decoded = await verify_firebase_id_token(firebase_token)
        except FirebaseError:
            raise AppException(
                status_code=401,
                code=401,
                message="Firebase ID 토큰이 유효하지 않거나 만료되었습니다.",
                error_key="INVALID_FIREBASE_TOKEN",
            )

        firebase_uid = decoded["uid"]

        user = await self._users.get_by_firebase_uid(firebase_uid)
        if user is None:
            raise AppException(
                status_code=404,
                code=404,
                message="가입되지 않은 사용자입니다. 회원가입이 필요합니다.",
                error_key="USER_NOT_FOUND",
            )

        await self._users.ensure_google_provider(
            user.id,
            firebase_uid,
            decoded.get("email"),
            bool(decoded.get("email_verified", False)),
        )

        access, refresh = await self._issue_session_tokens(user)

        return AuthTokensBundle(
            user=user,
            access_token=access,
            refresh_token=refresh,
            is_new_user=False,
        )

    async def refresh_access_tokens(self, *, refresh_token: str) -> tuple[str, str]:
        try:
            claims = decode_refresh_token_claims(refresh_token)
        except ExpiredSignatureError:
            raise AppException(
                status_code=401,
                code=401,
                message="유효하지 않거나 만료된 refreshToken입니다.",
                error_key="INVALID_REFRESH_TOKEN",
            )
        except JWTError:
            raise AppException(
                status_code=401,
                code=401,
                message="유효하지 않거나 만료된 refreshToken입니다.",
                error_key="INVALID_REFRESH_TOKEN",
            )

        if claims.get("type") != "refresh":
            raise AppException(
                status_code=401,
                code=401,
                message="유효하지 않거나 만료된 refreshToken입니다.",
                error_key="INVALID_REFRESH_TOKEN",
            )

        jti = claims.get("jti")
        sub = claims.get("sub")
        if not jti or not sub:
            raise AppException(
                status_code=401,
                code=401,
                message="유효하지 않거나 만료된 refreshToken입니다.",
                error_key="INVALID_REFRESH_TOKEN",
            )

        try:
            user_id = int(sub)
        except (TypeError, ValueError):
            raise AppException(
                status_code=401,
                code=401,
                message="유효하지 않거나 만료된 refreshToken입니다.",
                error_key="INVALID_REFRESH_TOKEN",
            )

        session_row = await self._auth.get_refresh_session(str(jti))
        if session_row is None:
            raise AppException(
                status_code=401,
                code=401,
                message="로그아웃 처리되었거나 폐기된 refreshToken입니다.",
                error_key="REVOKED_REFRESH_TOKEN",
            )

        if session_row.revoked_at is not None:
            raise AppException(
                status_code=401,
                code=401,
                message="로그아웃 처리되었거나 폐기된 refreshToken입니다.",
                error_key="REVOKED_REFRESH_TOKEN",
            )

        if session_row.user_id != user_id:
            raise AppException(
                status_code=401,
                code=401,
                message="유효하지 않거나 만료된 refreshToken입니다.",
                error_key="INVALID_REFRESH_TOKEN",
            )

        user = await self._users.get_by_id(user_id)
        if user is None:
            raise AppException(
                status_code=401,
                code=401,
                message="유효하지 않거나 만료된 refreshToken입니다.",
                error_key="INVALID_REFRESH_TOKEN",
            )

        await self._auth.revoke_refresh_session(str(jti))

        new_jti = str(uuid.uuid4())
        expires_at = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        new_access = create_access_token(user_id=user.id, firebase_uid=user.firebase_uid)
        new_refresh = create_refresh_token(user_id=user.id, jti=new_jti, expires_at=expires_at)
        await self._auth.persist_refresh_token(user.id, new_jti, expires_at)

        return new_access, new_refresh

    async def logout(self, *, refresh_token: str, access_user_id: int) -> None:
        try:
            claims = decode_refresh_token_for_logout(refresh_token)
        except JWTError:
            raise AppException(
                status_code=401,
                code=401,
                message="유효하지 않은 refreshToken입니다.",
                error_key="UNAUTHORIZED",
            )

        if claims.get("type") != "refresh":
            raise AppException(
                status_code=401,
                code=401,
                message="유효하지 않은 refreshToken입니다.",
                error_key="UNAUTHORIZED",
            )

        jti = claims.get("jti")
        sub = claims.get("sub")
        if not jti or not sub:
            raise AppException(
                status_code=401,
                code=401,
                message="유효하지 않은 refreshToken입니다.",
                error_key="UNAUTHORIZED",
            )

        try:
            user_id = int(sub)
        except (TypeError, ValueError):
            raise AppException(
                status_code=401,
                code=401,
                message="유효하지 않은 refreshToken입니다.",
                error_key="UNAUTHORIZED",
            )

        if user_id != access_user_id:
            raise AppException(
                status_code=401,
                code=401,
                message="인증 정보가 일치하지 않습니다.",
                error_key="UNAUTHORIZED",
            )

        session_row = await self._auth.get_refresh_session(str(jti))
        if session_row is None or session_row.user_id != access_user_id:
            raise AppException(
                status_code=401,
                code=401,
                message="유효하지 않은 refreshToken입니다.",
                error_key="UNAUTHORIZED",
            )

        if session_row.revoked_at is not None:
            raise AppException(
                status_code=401,
                code=401,
                message="이미 로그아웃된 refreshToken입니다.",
                error_key="UNAUTHORIZED",
            )

        await self._auth.revoke_refresh_session(str(jti))

    async def withdraw_account(
        self,
        *,
        access_user_id: int,
        access_firebase_uid: str,
    ) -> None:
        user = await self._users.get_by_id(access_user_id)
        if user is None or user.firebase_uid != access_firebase_uid:
            raise AppException(
                status_code=401,
                code=401,
                message="인증 정보가 일치하지 않습니다.",
                error_key="UNAUTHORIZED",
            )

        try:
            await delete_firebase_user(access_firebase_uid)
        except FirebaseError as e:
            raise AppException(
                status_code=500,
                code=500,
                message="Firebase 계정 삭제에 실패했습니다. 잠시 후 다시 시도해 주세요.",
            ) from e

        await self._auth.revoke_all_refresh_sessions_by_user(access_user_id)
        await self._users.delete(access_user_id)

    async def verify_residence(
        self,
        *,
        user_id: int,
        disaster_latitude: float,
        disaster_longitude: float,
        current_latitude: float,
        current_longitude: float,
        current_address: str | None,
    ) -> ResidenceVerificationResult:
        if not await self._auth.get_user_exists(user_id):
            raise AppException(
                status_code=401,
                code=401,
                message="인증 정보가 유효하지 않습니다.",
                error_key="UNAUTHORIZED",
            )

        self._validate_coordinate(disaster_latitude, disaster_longitude)
        self._validate_coordinate(current_latitude, current_longitude)

        now = self._utc_now_naive()
        await self._check_verify_cooldown(user_id, now)

        baseline = await self._auth.get_residence_baseline(user_id)
        if baseline is not None:
            disaster_latitude, disaster_longitude = baseline

        distance_km = self._haversine_km(
            disaster_latitude,
            disaster_longitude,
            current_latitude,
            current_longitude,
        )
        threshold_km = settings.RESIDENCE_VERIFY_RADIUS_KM
        if distance_km > threshold_km:
            await self._auth.log_residence_attempt(
                user_id=user_id,
                current_latitude=current_latitude,
                current_longitude=current_longitude,
                distance_km=distance_km,
                is_success=False,
                now=now,
            )
            return ResidenceVerificationResult(
                status="NONE",
                verified=False,
                distance_km=distance_km,
                threshold_km=threshold_km,
                verification_count=None,
                verified_at=None,
                expires_at=None,
                days_until_expiry=None,
                message=f"재난 발생 위치로부터 {int(threshold_km)}km를 벗어나 인증할 수 없습니다.",
            )

        expires_at = now + timedelta(days=settings.RESIDENCE_VERIFY_TTL_DAYS)
        result = await self._auth.verify_residence_first(
            user_id=user_id,
            disaster_latitude=disaster_latitude,
            disaster_longitude=disaster_longitude,
            current_latitude=current_latitude,
            current_longitude=current_longitude,
            current_address=current_address,
            distance_km=distance_km,
            threshold_km=threshold_km,
            now=now,
            expires_at=expires_at,
        )
        return ResidenceVerificationResult(
            status="VERIFIED",
            verified=True,
            distance_km=result.distance_km,
            threshold_km=result.threshold_km,
            verification_count=result.verification_count,
            verified_at=result.verified_at,
            expires_at=result.expires_at,
            days_until_expiry=None,
            message="거주지 인증이 완료되었습니다.",
        )

    async def reverify_residence(
        self,
        *,
        user_id: int,
        current_latitude: float,
        current_longitude: float,
        current_address: str | None,
    ) -> ResidenceVerificationResult:
        if not await self._auth.get_user_exists(user_id):
            raise AppException(
                status_code=401,
                code=401,
                message="인증 정보가 유효하지 않습니다.",
                error_key="UNAUTHORIZED",
            )

        self._validate_coordinate(current_latitude, current_longitude)
        now = self._utc_now_naive()
        await self._check_verify_cooldown(user_id, now)

        baseline = await self._auth.get_residence_baseline(user_id)
        if baseline is None:
            raise AppException(
                status_code=409,
                code=409,
                message="최초 거주지 인증이 필요합니다.",
                error_key="BASELINE_NOT_FOUND",
            )

        disaster_latitude, disaster_longitude = baseline
        distance_km = self._haversine_km(
            disaster_latitude,
            disaster_longitude,
            current_latitude,
            current_longitude,
        )
        threshold_km = settings.RESIDENCE_VERIFY_RADIUS_KM

        if distance_km > threshold_km:
            await self._auth.log_residence_attempt(
                user_id=user_id,
                current_latitude=current_latitude,
                current_longitude=current_longitude,
                distance_km=distance_km,
                is_success=False,
                now=now,
            )
            return ResidenceVerificationResult(
                status="NONE",
                verified=False,
                distance_km=distance_km,
                threshold_km=threshold_km,
                verification_count=None,
                verified_at=None,
                expires_at=None,
                days_until_expiry=None,
                message=f"재난 발생 위치로부터 {int(threshold_km)}km를 벗어나 인증할 수 없습니다.",
            )

        expires_at = now + timedelta(days=settings.RESIDENCE_VERIFY_TTL_DAYS)
        result = await self._auth.verify_residence_re(
            user_id=user_id,
            current_latitude=current_latitude,
            current_longitude=current_longitude,
            current_address=current_address,
            distance_km=distance_km,
            threshold_km=threshold_km,
            now=now,
            expires_at=expires_at,
        )
        if result is None:
            raise AppException(
                status_code=409,
                code=409,
                message="최초 거주지 인증이 필요합니다.",
                error_key="BASELINE_NOT_FOUND",
            )

        return ResidenceVerificationResult(
            status="VERIFIED",
            verified=True,
            distance_km=result.distance_km,
            threshold_km=result.threshold_km,
            verification_count=result.verification_count,
            verified_at=result.verified_at,
            expires_at=result.expires_at,
            days_until_expiry=None,
            message="거주지 재인증이 완료되었습니다.",
        )

    async def get_residence_verification(self, *, user_id: int) -> ResidenceVerificationResult:
        if not await self._auth.get_user_exists(user_id):
            raise AppException(
                status_code=401,
                code=401,
                message="인증 정보가 유효하지 않습니다.",
                error_key="UNAUTHORIZED",
            )
        row = await self._auth.get_residence_verification(user_id)
        return self._format_status_response(row, now=self._utc_now_naive())
