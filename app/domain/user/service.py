from urllib.parse import urlparse

from app.common.exceptions import AppException
from app.config import settings
from app.domain.user.entity import UserProfile
from app.domain.user.repository import UserRepository

_ALLOWED_FIREBASE_STORAGE_HOSTS = frozenset(
    {"firebasestorage.googleapis.com", "storage.googleapis.com"}
)
_ALLOWED_IMAGE_EXTENSIONS = (".jpg", ".jpeg", ".png", ".webp")


class UserService:
    def __init__(self, user_repo: UserRepository) -> None:
        self._users = user_repo

    async def get_me_profile(self, user_id: int) -> UserProfile:
        profile = await self._users.get_profile_by_user_id(user_id)
        if profile is None:
            raise AppException(
                status_code=404,
                code=404,
                message="사용자를 찾을 수 없습니다.",
                error_key="USER_NOT_FOUND",
            )
        return profile

    async def update_me_profile(
        self,
        *,
        user_id: int,
        nickname: str | None,
        address_name: str | None,
        household_type: str | None,
        profile_image_url: str | None,
    ) -> None:
        if household_type is not None and household_type not in {"SINGLE", "MULTI"}:
            raise AppException(
                status_code=400,
                code=400,
                message="householdType은 SINGLE 또는 MULTI만 허용됩니다.",
                error_key="VALIDATION_ERROR",
            )
        validated_url = None
        if profile_image_url is not None:
            validated_url = self._validate_profile_image_url(profile_image_url)
        await self._users.update_profile(
            user_id=user_id,
            nickname=nickname,
            address_name=address_name,
            profile_image_url=validated_url,
        )

    async def upload_profile_image(
        self,
        *,
        user_id: int,
        profile_image_url: str | None,
    ) -> str:
        if profile_image_url is None or not profile_image_url.strip():
            raise AppException(
                status_code=400,
                code=400,
                message="profileImageUrl이 필요합니다.",
                error_key="MISSING_PROFILE_IMAGE_URL",
            )
        validated = self._validate_profile_image_url(profile_image_url)
        await self._users.update_profile(user_id=user_id, profile_image_url=validated)
        return validated

    def _validate_profile_image_url(self, url: str) -> str:
        normalized = url.strip()
        parsed = urlparse(normalized)
        if parsed.scheme != "https" or not parsed.netloc:
            raise AppException(
                status_code=400,
                code=400,
                message="유효한 HTTPS URL이어야 합니다.",
                error_key="INVALID_PROFILE_IMAGE_URL",
            )

        host = parsed.hostname or ""
        if host not in _ALLOWED_FIREBASE_STORAGE_HOSTS:
            raise AppException(
                status_code=400,
                code=400,
                message="Firebase Storage URL만 허용됩니다.",
                error_key="INVALID_PROFILE_IMAGE_URL",
            )

        if settings.FIREBASE_STORAGE_BUCKET and settings.FIREBASE_STORAGE_BUCKET not in normalized:
            raise AppException(
                status_code=400,
                code=400,
                message="허용되지 않은 Storage bucket입니다.",
                error_key="INVALID_PROFILE_IMAGE_URL",
            )

        path_lower = parsed.path.lower()
        if not any(path_lower.endswith(ext) for ext in _ALLOWED_IMAGE_EXTENSIONS):
            raise AppException(
                status_code=400,
                code=400,
                message="jpg, png, webp 파일만 허용됩니다.",
                error_key="UNSUPPORTED_FILE_TYPE",
            )

        return normalized
