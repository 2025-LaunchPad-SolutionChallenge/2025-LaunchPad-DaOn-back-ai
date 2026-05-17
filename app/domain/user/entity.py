from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class User:
    """유저 도메인 스냅샷 (ORM과 분리)."""

    id: int
    firebase_uid: str
    name: str
    nickname: str | None
    profile_image_url: str | None
    birth_date: date | None
