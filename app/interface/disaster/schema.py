from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel


class CamelModel(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)


class DisasterType(str, Enum):
    FLOOD = "FLOOD"
    TYPHOON = "TYPHOON"
    EARTHQUAKE = "EARTHQUAKE"
    FIRE = "FIRE"


class SafetyStatus(str, Enum):
    SAFE = "SAFE"
    MINOR = "MINOR"
    DAMAGED = "DAMAGED"
    EMERGENCY = "EMERGENCY"


class ResidenceStatus(str, Enum):
    LIVABLE = "LIVABLE"
    PARTIAL_DAMAGE = "PARTIAL_DAMAGE"
    UNLIVABLE = "UNLIVABLE"


class InjuryLevel(str, Enum):
    NONE = "NONE"
    MINOR = "MINOR"
    SEVERE = "SEVERE"


class FloodLevel(str, Enum):
    NONE = "NONE"
    FRONT_YARD = "FRONT_YARD"
    FIRST_FLOOR = "FIRST_FLOOR"
    INSIDE_HOME = "INSIDE_HOME"


class WaterDrainStatus(str, Enum):
    STILL_PRESENT = "STILL_PRESENT"
    PARTIAL_DRAINED = "PARTIAL_DRAINED"
    MOSTLY_DRAINED = "MOSTLY_DRAINED"


class AftershockFeeling(str, Enum):
    NONE = "NONE"
    OCCASIONAL = "OCCASIONAL"
    CONTINUOUS = "CONTINUOUS"


class FireDamageScope(str, Enum):
    SMOKE_ONLY = "SMOKE_ONLY"
    PARTIAL_LOSS = "PARTIAL_LOSS"
    TOTAL_LOSS = "TOTAL_LOSS"


class SmokeInhalation(str, Enum):
    NONE = "NONE"
    MILD = "MILD"
    SEVERE = "SEVERE"


class AvailableTime(str, Enum):
    UNDER_ONE_HOUR = "UNDER_ONE_HOUR"
    ONE_TO_THREE_HOURS = "ONE_TO_THREE_HOURS"
    HALF_DAY = "HALF_DAY"
    ALL_DAY = "ALL_DAY"


class OnboardingRequest(CamelModel):
    disaster_id: int
    disaster_type: DisasterType
    safety_status: Optional[SafetyStatus] = None
    residence_status: ResidenceStatus
    injury_level: InjuryLevel
    damages: List[bool]
    flood_level: Optional[FloodLevel] = None
    water_drain_status: Optional[WaterDrainStatus] = None
    aftershock_feeling: Optional[AftershockFeeling] = None
    fire_damage_scope: Optional[FireDamageScope] = None
    smoke_inhalation: Optional[SmokeInhalation] = None


class OnboardingResponse(CamelModel):
    impact_id: int
    message: str


class UserCondition(CamelModel):
    can_go_out: bool
    available_time: AvailableTime


class ContextRequest(CamelModel):
    user_disaster_id: int
    user_condition: UserCondition


class ContextResponse(CamelModel):
    message: str
