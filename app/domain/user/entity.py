from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class User:
    """유저 도메인 스냅샷 (ORM과 분리)."""

    id: int
    firebase_uid: str
    name: str | None
    nickname: str | None
    profile_image_url: str | None
    birth_date: date | None


@dataclass(frozen=True)
class UserProfile:
    """프로필 조회 응답용 스냅샷."""

    user_id: int
    name: str | None
    nickname: str | None
    birth_date: date | None
    age: int | None
    profile_image_url: str | None
    residence_verified: bool
    address_name: str | None
