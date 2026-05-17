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

    firebaseToken: str = Field(..., min_length=1)
    name: str = Field(..., min_length=1)
    birthDate: date


class LoginRequest(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={"examples": [{"firebaseToken": "eyJhbGci..."}]},
    )

    firebaseToken: str = Field(..., min_length=1)


class RegisteredUserOut(BaseModel):
    id: int
    nickname: str | None
    profileImage: str | None


class AuthTokenResponse(BaseModel):
    user: RegisteredUserOut
    accessToken: str
    refreshToken: str
    isNewUser: bool


class RefreshRequest(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={"examples": [{"refreshToken": "eyJhbGci..."}]},
    )

    refreshToken: str = Field(..., min_length=1)


class RefreshResponse(BaseModel):
    accessToken: str
    refreshToken: str


class WithdrawRequest(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={"examples": [{"firebaseToken": "eyJhbGci..."}]},
    )

    firebaseToken: str = Field(..., min_length=1)


class MessageResponse(BaseModel):
    message: str
