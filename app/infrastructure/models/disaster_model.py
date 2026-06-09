"""Disaster 도메인 ORM — DDL 컬럼·테이블명과 동일."""

import enum
from datetime import datetime
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    Enum as SAEnum,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.infrastructure.models.base import TimestampMixin

if TYPE_CHECKING:
    from app.infrastructure.models.user_model import UserModel
    from app.infrastructure.models.recovery_model import (
        DailyStatusCheckModel,
        RecoveryFeatureModel,
        RecoveryOutputModel,
        RecoveryStageMasterModel,
    )
    from app.infrastructure.models.checklist_model import ChecklistItemModel


class RegistrationStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    EXPIRED = "EXPIRED"
    ARCHIVED = "ARCHIVED"


# [수정] SafetyStatus — safty → safety (오타 수정)
class SafetyStatus(str, enum.Enum):
    SAFE = "SAFE"
    MINOR = "MINOR"
    DAMAGED = "DAMAGED"
    EMERGENCY = "EMERGENCY"


class ResidenceStatus(str, enum.Enum):
    LIVABLE = "LIVABLE"
    PARTIAL_DAMAGE = "PARTIAL_DAMAGE"
    UNLIVABLE = "UNLIVABLE"


class InjuryLevel(str, enum.Enum):
    NONE = "NONE"
    MINOR = "MINOR"
    SEVERE = "SEVERE"


class AftershockFeeling(str, enum.Enum):
    NONE = "NONE"
    OCCASIONAL = "OCCASIONAL"
    CONTINUOUS = "CONTINUOUS"


class FireDamageScope(str, enum.Enum):
    SMOKE_ONLY = "SMOKE_ONLY"
    PARTIAL_LOSS = "PARTIAL_LOSS"
    TOTAL_LOSS = "TOTAL_LOSS"


class SmokeInhalation(str, enum.Enum):
    NONE = "NONE"
    MILD = "MILD"
    SEVERE = "SEVERE"


class FloodLevel(str, enum.Enum):
    NONE = "NONE"
    FRONT_YARD = "FRONT_YARD"
    FIRST_FLOOR = "FIRST_FLOOR"
    INSIDE_HOME = "INSIDE_HOME"


class WaterDrainStatus(str, enum.Enum):
    STILL_PRESENT = "STILL_PRESENT"
    PARTIAL_DRAINED = "PARTIAL_DRAINED"
    MOSTLY_DRAINED = "MOSTLY_DRAINED"


class AvailableTime(str, enum.Enum):
    UNDER_ONE_HOUR = "UNDER_ONE_HOUR"
    ONE_TO_THREE_HOURS = "ONE_TO_THREE_HOURS"
    # [수정] ALL_DAYHALF_DAY → ALL_DAY_HALF_DAY (DDL과 동일하게 언더스코어 추가)
    ALL_DAY_HALF_DAY = "ALL_DAY_HALF_DAY"


class DisasterTypeModel(Base):
    __tablename__ = "disaster_types"

    disaster_type_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    disaster_code: Mapped[str] = mapped_column(String(30), nullable=False, unique=True)
    # [수정] disaser_name → disaster_name (오타 수정)
    disaster_name: Mapped[Optional[str]] = mapped_column("disaster_name", String(255), nullable=True)
    description: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    user_disasters: Mapped[List["UserDisasterModel"]] = relationship(back_populates="disaster_type")


class UserDisasterModel(TimestampMixin, Base):
    __tablename__ = "user_disasters"

    user_disaster_id: Mapped[int] = mapped_column(
        "user__disaster_id", Integer, primary_key=True, autoincrement=True
    )
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("Users.user_id", ondelete="CASCADE"), nullable=False, index=True
    )
    disaster_type_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("disaster_types.disaster_type_id"), nullable=False
    )
    title: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    registered_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())
    ended_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    registration_status: Mapped[RegistrationStatus] = mapped_column(
        SAEnum(RegistrationStatus), nullable=False, default=RegistrationStatus.ACTIVE
    )
    recovery_stage_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("recovery_stage_masters.recovery_stage_id"), nullable=False
    )
    recovery_progress: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)

    user: Mapped["UserModel"] = relationship(back_populates="disasters")
    disaster_type: Mapped["DisasterTypeModel"] = relationship(back_populates="user_disasters")
    recovery_stage: Mapped["RecoveryStageMasterModel"] = relationship(back_populates="user_disasters")
    impact: Mapped[Optional["DisasterImpactModel"]] = relationship(
        back_populates="user_disaster", uselist=False, cascade="all, delete-orphan"
    )
    checklist_items: Mapped[List["ChecklistItemModel"]] = relationship(back_populates="user_disaster")
    daily_checks: Mapped[List["DailyStatusCheckModel"]] = relationship(back_populates="user_disaster")
    recovery_features: Mapped[List["RecoveryFeatureModel"]] = relationship(
        back_populates="user_disaster"
    )
    recovery_outputs: Mapped[List["RecoveryOutputModel"]] = relationship(back_populates="user_disaster")


class DisasterImpactModel(TimestampMixin, Base):
    __tablename__ = "disaster_impacts"

    impact_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_disaster_id: Mapped[int] = mapped_column(
        "user__disaster_id",
        Integer,
        ForeignKey("user_disasters.user__disaster_id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    # [수정] safty_status → safety_status (오타 수정)
    safety_status: Mapped[Optional[SafetyStatus]] = mapped_column(
        "safety_status", SAEnum(SafetyStatus), nullable=True
    )
    residence_status: Mapped[ResidenceStatus] = mapped_column(SAEnum(ResidenceStatus), nullable=False)
    injury_level: Mapped[InjuryLevel] = mapped_column(SAEnum(InjuryLevel), nullable=False)
    # [수정] canGoOut → can_go_out (camelCase → snake_case)
    can_go_out: Mapped[Optional[bool]] = mapped_column("can_go_out", Boolean, nullable=True)
    available_time: Mapped[Optional[AvailableTime]] = mapped_column(
        "available_time", SAEnum(AvailableTime), nullable=True
    )
    psychological_anxiety: Mapped[Optional[bool]] = mapped_column(
        "psychological_anxiety", Boolean, nullable=True
    )
    onboarding_risk_level: Mapped[Optional[int]] = mapped_column(
        "onboarding_risk_level", Integer, nullable=True
    )
    special_notes: Mapped[Optional[str]] = mapped_column("special_notes", Text, nullable=True)

    user_disaster: Mapped["UserDisasterModel"] = relationship(back_populates="impact")
    earthquake_detail: Mapped[Optional["EarthquakeImpactModel"]] = relationship(
        back_populates="impact", uselist=False, cascade="all, delete-orphan"
    )
    typhoon_detail: Mapped[Optional["TyphoonImpactModel"]] = relationship(
        back_populates="impact", uselist=False, cascade="all, delete-orphan"
    )
    fire_detail: Mapped[Optional["FireImpactModel"]] = relationship(
        back_populates="impact", uselist=False, cascade="all, delete-orphan"
    )
    flood_detail: Mapped[Optional["FloodImpactModel"]] = relationship(
        back_populates="impact", uselist=False, cascade="all, delete-orphan"
    )


class EarthquakeImpactModel(Base):
    __tablename__ = "earthquake_impacts"

    earth_impact_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    aftershock_feeling: Mapped[AftershockFeeling] = mapped_column(
        SAEnum(AftershockFeeling), nullable=False
    )
    building_crack: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    house_damage: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    vehicle_damage: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    electric_problem: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    water_problem: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    impact_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("disaster_impacts.impact_id", ondelete="CASCADE"), nullable=False, unique=True
    )

    impact: Mapped["DisasterImpactModel"] = relationship(back_populates="earthquake_detail")


class TyphoonImpactModel(Base):
    __tablename__ = "typhoon_impacts"

    typhoon_impact_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    roof_damage: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    window_damage: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    structure_damage: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    vehicle_damage: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    electric_problem: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    water_problem: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    impact_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("disaster_impacts.impact_id", ondelete="CASCADE"), nullable=False, unique=True
    )

    impact: Mapped["DisasterImpactModel"] = relationship(back_populates="typhoon_detail")


class FireImpactModel(Base):
    __tablename__ = "fire_impacts"

    fire_impact_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    fire_damage_scope: Mapped[FireDamageScope] = mapped_column(SAEnum(FireDamageScope), nullable=False)
    smoke_inhalation: Mapped[SmokeInhalation] = mapped_column(SAEnum(SmokeInhalation), nullable=False)
    house_damage: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    soot_damage: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    debris_exist: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    vehicle_damage: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    electric_problem: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    water_problem: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    impact_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("disaster_impacts.impact_id", ondelete="CASCADE"), nullable=False, unique=True
    )

    impact: Mapped["DisasterImpactModel"] = relationship(back_populates="fire_detail")


class FloodImpactModel(Base):
    __tablename__ = "flood_impacts"

    flood_impact_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    flood_level: Mapped[FloodLevel] = mapped_column(SAEnum(FloodLevel), nullable=False)
    water_drain_status: Mapped[WaterDrainStatus] = mapped_column(
        SAEnum(WaterDrainStatus), nullable=False
    )
    damage_house: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    damage_vehicle: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    electric_problem: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    water_problem: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    impact_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("disaster_impacts.impact_id", ondelete="CASCADE"), nullable=False, unique=True
    )

    impact: Mapped["DisasterImpactModel"] = relationship(back_populates="flood_detail")