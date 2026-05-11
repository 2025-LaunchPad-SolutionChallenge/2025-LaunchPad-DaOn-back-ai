from pydantic import BaseModel
from typing import Optional, Literal


# ENUM
SafetyStatus = Literal["SAFE", "MINOR", "DAMAGED", "EMERGENCY"]
ResidenceStatus = Literal["LIVABLE", "PARTIAL_DAMAGE", "UNLIVABLE"]
InjuryLevel = Literal["NONE", "MINOR", "SEVERE"]


class FloodDetail(BaseModel):
    floodLevel: Literal["FIRST_FLOOR", "SECOND_FLOOR", "FULL"]
    waterDrainStatus: Literal["DRAINED", "PARTIAL_DRAINED", "NOT_DRAINED"]
    damageHouse: bool
    damageVehicle: bool
    electricProblem: bool
    waterProblem: bool


class OnboardingRequest(BaseModel):
    disasterId: int
    safetyStatus: SafetyStatus
    residenceStatus: ResidenceStatus
    injuryLevel: InjuryLevel

    floodDetail: Optional[FloodDetail] = None


class OnboardingResponse(BaseModel):
    impactId: int
    message: str