from __future__ import annotations

from datetime import date as date_type
from datetime import datetime
from enum import Enum
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


class LocationResponse(BaseModel):
    latitude: float | None = Field(
        default=None,
        description="발생 위치 위도",
        examples=[37.5665],
    )
    longitude: float | None = Field(
        default=None,
        description="발생 위치 경도",
        examples=[126.9780],
    )
    address: str | None = Field(
        default=None,
        description="발생 위치 주소",
        examples=["서울특별시 중구"],
    )


class DisasterDetailResponse(BaseModel):
    userDisasterId: int
    title: str | None
    disasterType: DisasterTypeResponse
    status: str
    occurredAt: datetime
    endedAt: datetime | None
    location: LocationResponse | None = Field(
        default=None,
        description="발생 위치 정보(모두 비어 있으면 null)",
        examples=[{"latitude": 37.5665, "longitude": 126.9780, "address": "서울특별시 중구"}],
    )
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


class DisasterTypeEnum(str, Enum):
    FLOOD = "FLOOD"
    TYPHOON = "TYPHOON"
    EARTHQUAKE = "EARTHQUAKE"
    FIRE = "FIRE"


class SafetyStatusEnum(str, Enum):
    SAFE = "SAFE"
    MINOR = "MINOR"
    DAMAGED = "DAMAGED"
    EMERGENCY = "EMERGENCY"


class ResidenceStatusEnum(str, Enum):
    LIVABLE = "LIVABLE"
    PARTIAL_DAMAGE = "PARTIAL_DAMAGE"
    UNLIVABLE = "UNLIVABLE"


class InjuryLevelEnum(str, Enum):
    NONE = "NONE"
    MINOR = "MINOR"
    SEVERE = "SEVERE"


class FloodLevelEnum(str, Enum):
    NONE = "NONE"
    FRONT_YARD = "FRONT_YARD"
    FIRST_FLOOR = "FIRST_FLOOR"
    INSIDE_HOME = "INSIDE_HOME"


class WaterDrainStatusEnum(str, Enum):
    STILL_PRESENT = "STILL_PRESENT"
    PARTIAL_DRAINED = "PARTIAL_DRAINED"
    MOSTLY_DRAINED = "MOSTLY_DRAINED"


class AftershockFeelingEnum(str, Enum):
    NONE = "NONE"
    OCCASIONAL = "OCCASIONAL"
    CONTINUOUS = "CONTINUOUS"


class FireDamageScopeEnum(str, Enum):
    SMOKE_ONLY = "SMOKE_ONLY"
    PARTIAL_LOSS = "PARTIAL_LOSS"
    TOTAL_LOSS = "TOTAL_LOSS"


class SmokeInhalationEnum(str, Enum):
    NONE = "NONE"
    MILD = "MILD"
    SEVERE = "SEVERE"


class OnboardingRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    disasterType: DisasterTypeEnum = Field(..., description="재난 유형 코드")
    latitude: float | None = Field(default=None, description="발생 위치 위도")
    longitude: float | None = Field(default=None, description="발생 위치 경도")
    address: str | None = Field(default=None, description="발생 위치 주소")
    safetyStatus: SafetyStatusEnum | None = Field(default=None, description="안전 상태")
    residenceStatus: ResidenceStatusEnum = Field(..., description="거주지 상태")
    injuryLevel: InjuryLevelEnum = Field(..., description="부상 정도")
    damages: list[bool] = Field(..., description="재난 유형별 피해 체크 배열")
    floodLevel: FloodLevelEnum | None = Field(default=None, description="홍수 침수 정도")
    waterDrainStatus: WaterDrainStatusEnum | None = Field(default=None, description="홍수 배수 상태")
    aftershockFeeling: AftershockFeelingEnum | None = Field(default=None, description="지진 여진 체감")
    fireDamageScope: FireDamageScopeEnum | None = Field(default=None, description="화재 피해 범위")
    smokeInhalation: SmokeInhalationEnum | None = Field(default=None, description="연기 흡입 정도")


class OnboardingResponse(BaseModel):
    userDisasterId: int = Field(..., description="생성된 사용자 재난 ID")
    impactId: int = Field(..., description="생성된 재난 영향 ID")
    onboardingRiskLevel: int = Field(..., description="온보딩 위험도(1~3)")
    message: str = Field(..., description="처리 결과 메시지")


class RecoveryStageDetailResponse(BaseModel):
    stageId: int = Field(..., description="단계 번호")
    stageCode: str = Field(..., description="회복 단계 코드")
    stageName: str = Field(..., description="회복 단계 이름")
    description: str = Field(..., description="단계 설명")


class RecoveryGraphPointResponse(BaseModel):
    date: date_type = Field(..., description="기준 일자")
    recoveryScore: float | None = Field(default=None, description="회복 점수 (0.0~100.0), 피처 데이터 없으면 null")
    stageCode: str = Field(..., description="해당 일자의 단계 코드")
    stageName: str = Field(..., description="해당 일자의 단계 이름")


class RecoveryGraphResponse(BaseModel):
    userDisasterId: int = Field(..., description="대상 재난 ID")
    points: list[RecoveryGraphPointResponse] = Field(..., description="회복 단계 이력")


class RecoveryProgressResponse(BaseModel):
    userDisasterId: int = Field(..., description="대상 재난 ID")
    recoveryScore: float = Field(..., description="현재 회복 점수 (0.0~100.0)")
    stageCode: str = Field(..., description="현재 단계 코드")
    stageName: str = Field(..., description="현재 단계 이름")
    stageDescription: str = Field(..., description="현재 단계 설명")
