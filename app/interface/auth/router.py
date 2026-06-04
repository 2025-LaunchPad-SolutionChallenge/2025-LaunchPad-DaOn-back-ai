from fastapi import APIRouter, Depends

from app.common.dependencies import get_auth_service, get_current_access_payload
from app.common.swagger import error_responses
from app.domain.auth.service import AuthService
from app.interface.auth.schema import (
    AuthTokenResponse,
    LoginRequest,
    MessageResponse,
    RefreshRequest,
    RefreshResponse,
    RegisterRequest,
    RegisteredUserOut,
)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    "/register",
    response_model=AuthTokenResponse,
    summary="회원가입",
    description=(
        "Firebase ID 토큰으로 회원가입합니다. "
        "이미 가입된 Firebase 계정이면 로그인과 동일하게 토큰을 발급합니다."
    ),
    responses=error_responses(400, 401, 409, 500),
)
async def register(
    req: RegisterRequest,
    auth_service: AuthService = Depends(get_auth_service),
) -> AuthTokenResponse:
    result = await auth_service.register(
        firebase_token=req.firebaseToken,
        name=req.name,
        birth_date=req.birthDate,
    )

    return AuthTokenResponse(
        user=RegisteredUserOut(
            id=result.user.id,
            nickname=result.user.nickname,
            profileImage=result.user.profile_image_url,
        ),
        accessToken=result.access_token,
        refreshToken=result.refresh_token,
        isNewUser=result.is_new_user,
    )


@router.post(
    "/login",
    response_model=AuthTokenResponse,
    summary="로그인",
    description="Firebase ID 토큰으로 로그인하고 JWT access/refresh 토큰을 발급합니다.",
    responses=error_responses(400, 401, 404, 500),
)
async def login(
    req: LoginRequest,
    auth_service: AuthService = Depends(get_auth_service),
) -> AuthTokenResponse:
    result = await auth_service.login(firebase_token=req.firebaseToken)

    return AuthTokenResponse(
        user=RegisteredUserOut(
            id=result.user.id,
            nickname=result.user.nickname,
            profileImage=result.user.profile_image_url,
        ),
        accessToken=result.access_token,
        refreshToken=result.refresh_token,
        isNewUser=result.is_new_user,
    )


@router.post(
    "/refresh",
    response_model=RefreshResponse,
    summary="토큰 갱신",
    description="리프레시 토큰으로 access/refresh 토큰을 재발급합니다.",
    responses=error_responses(400, 401, 500),
)
async def refresh_tokens(
    req: RefreshRequest,
    auth_service: AuthService = Depends(get_auth_service),
) -> RefreshResponse:
    access, refresh = await auth_service.refresh_access_tokens(refresh_token=req.refreshToken)

    return RefreshResponse(accessToken=access, refreshToken=refresh)


@router.post(
    "/logout",
    response_model=MessageResponse,
    summary="로그아웃",
    description=(
        "액세스 토큰(Bearer)과 리프레시 토큰(본문)으로 로그아웃합니다. "
        "리프레시 토큰 세션이 무효화됩니다."
    ),
    responses=error_responses(400, 401, 500),
)
async def logout(
    req: RefreshRequest,
    auth_service: AuthService = Depends(get_auth_service),
    payload: dict = Depends(get_current_access_payload),
) -> MessageResponse:
    access_uid = int(payload["sub"])
    await auth_service.logout(refresh_token=req.refreshToken, access_user_id=access_uid)
    return MessageResponse(message="로그아웃되었습니다.")


@router.delete(
    "/withdraw",
    response_model=MessageResponse,
    summary="회원탈퇴",
    description="액세스 토큰(Bearer)으로 본인 계정을 삭제합니다. 되돌릴 수 없습니다.",
    responses=error_responses(401, 404, 500),
)
async def withdraw(
    auth_service: AuthService = Depends(get_auth_service),
    payload: dict = Depends(get_current_access_payload),
) -> MessageResponse:
    access_uid = int(payload["sub"])
    access_fb = str(payload["firebase_uid"])
    await auth_service.withdraw_account(
        access_user_id=access_uid,
        access_firebase_uid=access_fb,
    )
    return MessageResponse(message="계정이 삭제되었습니다.")
