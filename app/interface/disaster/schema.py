from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class RecoveryStageResponse(BaseModel):
    stageCode: str
    stageName: str


class DisasterListItemResponse(BaseModel):
    userDisasterId: int
    title: str | None
    disasterTypeCode: str
    disasterTypeName: str | None
    status: str
    occurredAt: datetime
    endedAt: datetime | None
    recoveryStage: RecoveryStageResponse
    recoveryProgress: float


class DisasterListResponse(BaseModel):
    content: list[DisasterListItemResponse]
    page: int
    size: int
    totalElements: int


class DisasterTypeResponse(BaseModel):
    disasterTypeId: int
    disasterCode: str
    name: str | None


class DisasterImpactResponse(BaseModel):
    safetyStatus: str | None
    residenceStatus: str | None
    injuryLevel: str | None
    canGoOut: bool | None
    availableTime: str | None


class DisasterDetailResponse(BaseModel):
    userDisasterId: int
    title: str | None
    disasterType: DisasterTypeResponse
    status: str
    occurredAt: datetime
    endedAt: datetime | None
    recoveryStage: RecoveryStageResponse
    recoveryProgress: float
    impact: DisasterImpactResponse | None
    detail: dict[str, Any] | None


class DisasterImpactPatchRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    safetyStatus: str | None = None
    residenceStatus: str | None = None
    injuryLevel: str | None = None
    canGoOut: bool | None = None
    availableTime: str | None = None


class DisasterPatchRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str | None = None
    occurredAt: datetime | None = None
    impact: DisasterImpactPatchRequest | None = None
    detail: dict[str, Any] | None = None


class DisasterPatchResponse(BaseModel):
    userDisasterId: int
    message: str


class DisasterCloseRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    action: Literal["CLOSE", "ARCHIVE"] = Field(..., description="상태 전환 액션")
    endedAt: datetime | None = None


class DisasterCloseResponse(BaseModel):
    userDisasterId: int
    status: str
    endedAt: datetime
    message: str
