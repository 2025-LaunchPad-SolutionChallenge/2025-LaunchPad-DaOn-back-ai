"""Recovery 도메인 ORM — DDL 컬럼·테이블명과 동일."""

from datetime import date, datetime
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import BigInteger, Boolean, Date, DateTime, Float, ForeignKey, Integer, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.infrastructure.models.base import TimestampMixin

if TYPE_CHECKING:
    from app.infrastructure.models.disaster_model import UserDisasterModel


class RecoveryStageMasterModel(TimestampMixin, Base):
    __tablename__ = "recovery_stage_masters"

    recovery_stage_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    stage_code: Mapped[str] = mapped_column(String(30), nullable=False, unique=True)
    stage_name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    user_disasters: Mapped[List["UserDisasterModel"]] = relationship(back_populates="recovery_stage")


class RecoveryOutputModel(Base):
    __tablename__ = "recovery_outputs"
    __table_args__ = (
        UniqueConstraint("user__disaster_id", "state_date", name="uq_recovery_output_user_date"),
    )

    output_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_disaster_id: Mapped[int] = mapped_column(
        "user__disaster_id",
        Integer,
        ForeignKey("user_disasters.user__disaster_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    state_date: Mapped[date] = mapped_column(Date, nullable=False)
    predicted_stage: Mapped[str] = mapped_column(String(20), nullable=False)
    raw_stage: Mapped[str] = mapped_column(String(20), nullable=False)
    task_1: Mapped[str] = mapped_column(String(255), nullable=False)
    task_2: Mapped[str] = mapped_column(String(255), nullable=False)
    task_3: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())

    user_disaster: Mapped["UserDisasterModel"] = relationship(back_populates="recovery_outputs")


class RecoveryFeatureModel(Base):
    __tablename__ = "recovery_features"

    feature_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_disaster_id: Mapped[int] = mapped_column(
        "user__disaster_id",
        Integer,
        ForeignKey("user_disasters.user__disaster_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    feature_date: Mapped[date] = mapped_column(Date, nullable=False)
    onboarding_risk_level: Mapped[int] = mapped_column(Integer, nullable=False)
    avg_7d_status_score: Mapped[float] = mapped_column(Float, nullable=False)
    avg_7d_action_score: Mapped[float] = mapped_column(Float, nullable=False)
    outing_capability: Mapped[float] = mapped_column(Float, nullable=False)
    avg_7d_task_completion_rate: Mapped[float] = mapped_column(Float, nullable=False)
    avg_7d_available_time: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    avg_7d_need_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    recent_3d_need_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    recent_3d_no_outing_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    recent_3d_zero_task_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())

    user_disaster: Mapped["UserDisasterModel"] = relationship(back_populates="recovery_features")


class DailyStatusCheckModel(Base):
    __tablename__ = "daily_status_checks"

    daily_check_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_disaster_id: Mapped[int] = mapped_column(
        "user__disaster_id",
        Integer,
        ForeignKey("user_disasters.user__disaster_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    check_date: Mapped[date] = mapped_column(Date, nullable=False)
    emotion_score: Mapped[int] = mapped_column(Integer, nullable=False)
    condition_score: Mapped[int] = mapped_column(Integer, nullable=False)
    action_score: Mapped[float] = mapped_column(Float, nullable=False)
    change_score: Mapped[int] = mapped_column(Integer, nullable=False)
    need_score: Mapped[float] = mapped_column(Float, nullable=False)
    available_time: Mapped[int] = mapped_column(Integer, nullable=False)
    can_go_out: Mapped[bool] = mapped_column(Boolean, nullable=False)

    user_disaster: Mapped["UserDisasterModel"] = relationship(back_populates="daily_checks")