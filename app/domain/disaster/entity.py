from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any


@dataclass(frozen=True)
class RecoveryStageSnapshot:
    stage_code: str
    stage_name: str


@dataclass(frozen=True)
class DisasterListItem:
    user_disaster_id: int
    title: str | None
    disaster_type_code: str
    disaster_type_name: str | None
    status: str
    occurred_at: datetime
    ended_at: datetime | None
    recovery_stage: RecoveryStageSnapshot
    recovery_progress: float


@dataclass(frozen=True)
class DisasterListPage:
    content: list[DisasterListItem]
    page: int
    size: int
    total_elements: int


@dataclass(frozen=True)
class DisasterTypeSnapshot:
    disaster_type_id: int
    disaster_code: str
    name: str | None


@dataclass(frozen=True)
class ImpactSnapshot:
    safety_status: str | None
    residence_status: str | None
    injury_level: str | None
    can_go_out: bool | None
    available_time: str | None


@dataclass(frozen=True)
class DisasterDetail:
    user_disaster_id: int
    title: str | None
    disaster_type: DisasterTypeSnapshot
    status: str
    occurred_at: datetime
    ended_at: datetime | None
    recovery_stage: RecoveryStageSnapshot
    recovery_progress: float
    impact: ImpactSnapshot | None
    detail: dict[str, Any] | None
