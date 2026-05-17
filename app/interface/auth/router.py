from fastapi import APIRouter, Body, Depends

from app.common.dependencies import get_auth_service, get_current_access_payload
from app.domain.auth.service import AuthService
from app.interface.auth.schema import (
    AuthTokenResponse,
    LoginRequest,
    MessageResponse,
    RefreshRequest,
    RefreshResponse,
    RegisterRequest,
    RegisteredUserOut,
    WithdrawRequest,
)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=AuthTokenResponse)
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


@router.post("/login", response_model=AuthTokenResponse)
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


@router.post("/refresh", response_model=RefreshResponse)
async def refresh_tokens(
    req: RefreshRequest,
    auth_service: AuthService = Depends(get_auth_service),
) -> RefreshResponse:
    access, refresh = await auth_service.refresh_access_tokens(refresh_token=req.refreshToken)

    return RefreshResponse(accessToken=access, refreshToken=refresh)


@router.post("/logout", response_model=MessageResponse)
async def logout(
    req: RefreshRequest,
    auth_service: AuthService = Depends(get_auth_service),
    payload: dict = Depends(get_current_access_payload),
) -> MessageResponse:
    access_uid = int(payload["sub"])
    await auth_service.logout(refresh_token=req.refreshToken, access_user_id=access_uid)
    return MessageResponse(message="로그아웃되었습니다.")


@router.delete("/withdraw", response_model=MessageResponse)
async def withdraw(
    req: WithdrawRequest = Body(...),
    auth_service: AuthService = Depends(get_auth_service),
    payload: dict = Depends(get_current_access_payload),
) -> MessageResponse:
    access_uid = int(payload["sub"])
    access_fb = str(payload["firebase_uid"])
    await auth_service.withdraw_account(
        firebase_token=req.firebaseToken,
        access_user_id=access_uid,
        access_firebase_uid=access_fb,
    )
    return MessageResponse(message="계정이 삭제되었습니다.")
