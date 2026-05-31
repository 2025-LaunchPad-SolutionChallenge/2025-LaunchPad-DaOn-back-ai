from datetime import date

from pydantic import BaseModel, ConfigDict, Field


_EX_REGISTER = {
    "firebaseToken": "eyJhbGci...",
}


class RegisterRequest(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={"examples": [_EX_REGISTER]},
    )

    firebaseToken: str = Field(..., min_length=1)
    name: str | None = Field(default=None, min_length=1)
    birthDate: date | None = None


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


class MessageResponse(BaseModel):
    message: str
