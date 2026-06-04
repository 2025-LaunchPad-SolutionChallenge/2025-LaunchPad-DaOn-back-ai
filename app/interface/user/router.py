from typing import Annotated, Any

from fastapi import APIRouter, Depends, Form
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.dependencies import get_db
from app.common.swagger import error_responses
from app.dependencies.auth import get_current_user
from app.domain.user.service import UserService
from app.infrastructure.repositories.user_repository import SqlAlchemyUserRepository
from app.interface.user.schema import (
    MeProfileResponse,
    MessageResponse,
    ProfileImageUploadRequest,
    ProfileImageUploadResponse,
)

router = APIRouter(prefix="/users", tags=["users"])


def get_user_service(db: AsyncSession = Depends(get_db)) -> UserService:
    return UserService(SqlAlchemyUserRepository(db))


@router.get(
    "/me",
    response_model=MeProfileResponse,
    summary="내 프로필 조회",
    description="액세스 토큰(Bearer)으로 로그인한 사용자의 프로필 정보를 조회합니다.",
    responses=error_responses(401, 404, 500),
)
async def get_me(
    current_user: dict[str, Any] = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service),
) -> MeProfileResponse:
    user_id = int(current_user["sub"])
    profile = await user_service.get_me_profile(user_id=user_id)
    return MeProfileResponse(
        userId=profile.user_id,
        name=profile.name,
        nickname=profile.nickname,
        birthDate=profile.birth_date,
        age=profile.age,
        profileImage=profile.profile_image_url,
        residenceVerified=profile.residence_verified,
        addressName=profile.address_name,
    )


@router.put(
    "/me",
    response_model=MessageResponse,
    summary="내 프로필 수정",
    description=(
        "`multipart/form-data`로 프로필을 수정합니다. "
        "변경할 필드만 전송하면 됩니다. "
        "프로필 이미지는 Firebase Storage URL(`profileImageUrl`)로 전달합니다."
    ),
    responses=error_responses(400, 401, 404, 500),
)
async def update_me(
    nickname: Annotated[str | None, Form(description="닉네임")] = None,
    addressName: Annotated[str | None, Form(description="거주지 주소명")] = None,
    householdType: Annotated[str | None, Form(description="가구 유형 (SINGLE | MULTI)")] = None,
    profileImageUrl: Annotated[
        str | None,
        Form(description="Firebase Storage에 업로드된 프로필 이미지 URL"),
    ] = None,
    current_user: dict[str, Any] = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service),
) -> MessageResponse:
    user_id = int(current_user["sub"])
    await user_service.update_me_profile(
        user_id=user_id,
        nickname=nickname,
        address_name=addressName,
        household_type=householdType,
        profile_image_url=profileImageUrl,
    )
    return MessageResponse(message="프로필이 수정되었습니다")


@router.post(
    "/me/profile-image",
    response_model=ProfileImageUploadResponse,
    summary="프로필 이미지 URL 저장",
    description=(
        "프론트에서 Firebase Storage에 업로드한 이미지 URL을 전달하면 "
        "URL을 검증한 뒤 사용자 프로필에 저장합니다."
    ),
    responses=error_responses(400, 401, 404, 500),
)
async def upload_profile_image(
    req: ProfileImageUploadRequest,
    current_user: dict[str, Any] = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service),
) -> ProfileImageUploadResponse:
    user_id = int(current_user["sub"])
    image_url = await user_service.upload_profile_image(
        user_id=user_id,
        profile_image_url=req.profileImageUrl,
    )
    return ProfileImageUploadResponse(profileImageUrl=image_url)
