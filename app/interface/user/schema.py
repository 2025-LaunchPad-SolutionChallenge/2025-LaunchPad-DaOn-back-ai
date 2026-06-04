from datetime import date

from pydantic import BaseModel, ConfigDict, Field

_FIREBASE_STORAGE_URL_EXAMPLE = (
    "https://firebasestorage.googleapis.com/v0/b/my-project.appspot.com/o/"
    "profile-images%2Favatar.png?alt=media&token=abc123"
)


class MeProfileResponse(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "userId": 1,
                    "name": "홍길동",
                    "nickname": "길동",
                    "birthDate": "1995-03-15",
                    "age": 30,
                    "profileImage": _FIREBASE_STORAGE_URL_EXAMPLE,
                    "residenceVerified": False,
                    "addressName": "서울특별시 강남구",
                }
            ]
        }
    )

    userId: int = Field(..., description="사용자 ID")
    name: str | None = Field(default=None, description="실명")
    nickname: str | None = Field(default=None, description="닉네임")
    birthDate: date | None = Field(default=None, description="생년월일")
    age: int | None = Field(default=None, description="만 나이")
    profileImage: str | None = Field(default=None, description="프로필 이미지 URL")
    residenceVerified: bool = Field(..., description="거주지 인증 여부")
    addressName: str | None = Field(default=None, description="거주지 주소명")


class MessageResponse(BaseModel):
    message: str = Field(..., description="처리 결과 메시지")


class ProfileImageUploadRequest(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "examples": [{"profileImageUrl": _FIREBASE_STORAGE_URL_EXAMPLE}]
        },
    )

    profileImageUrl: str = Field(
        ...,
        min_length=1,
        description="프론트에서 Firebase Storage에 업로드한 이미지 URL",
    )


class ProfileImageUploadResponse(BaseModel):
    profileImageUrl: str = Field(..., description="저장된 프로필 이미지 URL")
