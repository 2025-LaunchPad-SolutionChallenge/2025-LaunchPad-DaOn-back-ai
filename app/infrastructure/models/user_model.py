"""User 도메인 ORM — DDL(ERD) 컬럼·테이블명과 동일하게 매핑."""

import enum
from datetime import date, datetime
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import Boolean, Date, DateTime, Enum as SAEnum, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.infrastructure.models.base import TimestampMixin

if TYPE_CHECKING:
    from app.infrastructure.models.disaster_model import UserDisasterModel
    from app.infrastructure.models.community_model import CommunityProfileModel


# [수정] varification → verification
class VerificationStatus(str, enum.Enum):
    PENDING = "PENDING"
    VERIFIED = "VERIFIED"
    EXPIRED = "EXPIRED"


class ProviderType(str, enum.Enum):
    GOOGLE = "GOOGLE"
    EMAIL = "EMAIL"
    FACEBOOK = "FACEBOOK"


class UserModel(TimestampMixin, Base):
    __tablename__ = "Users"

    user_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    nickname: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    birth_date: Mapped[date] = mapped_column(Date, nullable=False)
    profile_image_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    firebase_uid: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    residence_verified: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    auth_providers: Mapped[List["UserAuthProviderModel"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    residences: Mapped[List["UserResidenceModel"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    setting: Mapped[Optional["UserSettingModel"]] = relationship(
        back_populates="user", uselist=False, cascade="all, delete-orphan"
    )
    disasters: Mapped[List["UserDisasterModel"]] = relationship(back_populates="user")
    community_profile: Mapped[Optional["CommunityProfileModel"]] = relationship(
        back_populates="user", uselist=False, cascade="all, delete-orphan"
    )


class UserAuthProviderModel(TimestampMixin, Base):
    __tablename__ = "user_auth_provider"

    auth_provider_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("Users.user_id", ondelete="CASCADE"), nullable=False, index=True
    )
    provider_type: Mapped[ProviderType] = mapped_column(SAEnum(ProviderType), nullable=False)
    provider_uid: Mapped[str] = mapped_column(String(255), nullable=False)
    provider_email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    is_verified: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    connected_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())
    last_login_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    user: Mapped["UserModel"] = relationship(back_populates="auth_providers")


class UserResidenceModel(TimestampMixin, Base):
    __tablename__ = "user_residences"

    residence_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("Users.user_id", ondelete="CASCADE"), nullable=False, index=True
    )
    address_name: Mapped[str] = mapped_column(String(200), nullable=False)
    region_code: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    # [수정] varification_status → verification_status (컬럼명 오타 수정)
    verification_status: Mapped[Optional[VerificationStatus]] = mapped_column(
        "verification_status", SAEnum(VerificationStatus), nullable=True
    )
    verified_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    user: Mapped["UserModel"] = relationship(back_populates="residences")


class UserSettingModel(TimestampMixin, Base):
    __tablename__ = "user_settings"

    user_setting_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("Users.user_id", ondelete="CASCADE"), nullable=False, unique=True
    )
    allow_push_notification: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    user_disaster_id: Mapped[int] = mapped_column(
        "user__disaster_id",
        Integer,
        ForeignKey("user_disasters.user__disaster_id"),
        nullable=False,
    )

    user: Mapped["UserModel"] = relationship(back_populates="setting")