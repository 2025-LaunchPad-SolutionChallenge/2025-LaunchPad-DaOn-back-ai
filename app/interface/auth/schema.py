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


class ResidenceVerifyRequest(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "examples": [
                {
                    "disasterLatitude": 37.5665,
                    "disasterLongitude": 126.9780,
                    "currentLatitude": 37.57,
                    "currentLongitude": 126.982,
                    "currentAddress": "서울특별시 중구 ...",
                }
            ]
        },
    )

    disasterLatitude: float = Field(..., description="재난 기준점 위도(최초 1회만 반영)")
    disasterLongitude: float = Field(..., description="재난 기준점 경도(최초 1회만 반영)")
    currentLatitude: float = Field(..., description="현재 위치 위도")
    currentLongitude: float = Field(..., description="현재 위치 경도")
    currentAddress: str | None = Field(default=None, description="현재 주소 문자열")


class ResidenceReverifyRequest(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "examples": [
                {
                    "currentLatitude": 37.5705,
                    "currentLongitude": 126.9815,
                    "currentAddress": "서울특별시 중구 ...",
                }
            ]
        },
    )

    currentLatitude: float = Field(..., description="현재 위치 위도")
    currentLongitude: float = Field(..., description="현재 위치 경도")
    currentAddress: str | None = Field(default=None, description="현재 주소 문자열")


class ResidenceVerificationResponse(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "status": "VERIFIED",
                    "verified": True,
                    "distanceKm": 0.52,
                    "thresholdKm": 10.0,
                    "verificationCount": 1,
                    "verifiedAt": "2026-02-24T09:41:00Z",
                    "expiresAt": "2026-03-26T09:41:00Z",
                    "daysUntilExpiry": 30,
                    "message": "거주지 인증이 완료되었습니다.",
                }
            ]
        }
    )

    status: str = Field(..., description="인증 상태(VERIFIED | EXPIRED | NONE)")
    verified: bool = Field(..., description="현재 유효한 인증 여부")
    distanceKm: float | None = Field(default=None, description="거리(km)")
    thresholdKm: float | None = Field(default=None, description="인증 허용 반경(km)")
    verificationCount: int | None = Field(default=None, description="누적 성공 인증 횟수")
    verifiedAt: str | None = Field(default=None, description="마지막 성공 인증 시각(ISO8601)")
    expiresAt: str | None = Field(default=None, description="인증 만료 시각(ISO8601)")
    daysUntilExpiry: int | None = Field(default=None, description="만료까지 남은 일수")
    message: str | None = Field(default=None, description="상태 메시지")
