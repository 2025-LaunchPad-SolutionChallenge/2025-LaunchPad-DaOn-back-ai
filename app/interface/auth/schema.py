from datetime import date

from pydantic import BaseModel, ConfigDict, Field


_EX_REGISTER = {
    "firebaseToken": "eyJhbGci...",
    "name": "홍길동",
    "birthDate": "1995-03-15",
}


class RegisterRequest(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={"examples": [_EX_REGISTER]},
    )

    firebaseToken: str = Field(..., min_length=1, description="Firebase ID 토큰")
    name: str | None = Field(default=None, min_length=1, description="실명 (신규 가입 시)")
    birthDate: date | None = Field(default=None, description="생년월일 (YYYY-MM-DD, 신규 가입 시)")


class LoginRequest(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={"examples": [{"firebaseToken": "eyJhbGci..."}]},
    )

    firebaseToken: str = Field(..., min_length=1, description="Firebase ID 토큰")


class RegisteredUserOut(BaseModel):
    id: int = Field(..., description="사용자 ID")
    nickname: str | None = Field(default=None, description="닉네임")
    profileImage: str | None = Field(default=None, description="프로필 이미지 URL")


class AuthTokenResponse(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "user": {"id": 1, "nickname": "홍길동", "profileImage": None},
                    "accessToken": "eyJhbGci...",
                    "refreshToken": "eyJhbGci...",
                    "isNewUser": True,
                }
            ]
        }
    )

    user: RegisteredUserOut
    accessToken: str = Field(..., description="JWT 액세스 토큰")
    refreshToken: str = Field(..., description="JWT 리프레시 토큰")
    isNewUser: bool = Field(..., description="신규 가입 여부")


class RefreshRequest(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={"examples": [{"refreshToken": "eyJhbGci..."}]},
    )

    refreshToken: str = Field(..., min_length=1, description="JWT 리프레시 토큰")


class RefreshResponse(BaseModel):
    accessToken: str = Field(..., description="갱신된 JWT 액세스 토큰")
    refreshToken: str = Field(..., description="갱신된 JWT 리프레시 토큰")


class MessageResponse(BaseModel):
    message: str = Field(..., description="처리 결과 메시지")
