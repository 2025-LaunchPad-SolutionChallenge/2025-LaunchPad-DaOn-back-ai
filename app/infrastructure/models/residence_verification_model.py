from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.infrastructure.models.base import TimestampMixin

if TYPE_CHECKING:
    from app.infrastructure.models.user_model import UserModel


class ResidenceVerificationModel(TimestampMixin, Base):
    __tablename__ = "residence_verification"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("Users.user_id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    disaster_latitude: Mapped[float] = mapped_column(Numeric(10, 7), nullable=False)
    disaster_longitude: Mapped[float] = mapped_column(Numeric(10, 7), nullable=False)
    last_current_lat: Mapped[float] = mapped_column(Numeric(10, 7), nullable=False)
    last_current_lng: Mapped[float] = mapped_column(Numeric(10, 7), nullable=False)
    last_address: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    last_distance_km: Mapped[float] = mapped_column(Numeric(8, 3), nullable=False)
    threshold_km: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False)
    verification_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    verified_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    user: Mapped["UserModel"] = relationship()


class ResidenceVerificationLogModel(TimestampMixin, Base):
    __tablename__ = "residence_verification_log"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("Users.user_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    current_latitude: Mapped[float] = mapped_column(Numeric(10, 7), nullable=False)
    current_longitude: Mapped[float] = mapped_column(Numeric(10, 7), nullable=False)
    distance_km: Mapped[float] = mapped_column(Numeric(8, 3), nullable=False)
    is_success: Mapped[bool] = mapped_column(Boolean, nullable=False)
    verified_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    user: Mapped["UserModel"] = relationship()
