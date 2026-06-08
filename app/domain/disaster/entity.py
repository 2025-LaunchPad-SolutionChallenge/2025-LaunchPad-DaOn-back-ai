from dataclasses import dataclass
from typing import Optional


@dataclass
class DisasterImpact:
    user_disaster_id: int
    residence_status: str
    injury_level: str
    impact_id: Optional[int] = None
    safety_status: Optional[str] = None
    can_go_out: Optional[bool] = None
    available_time: Optional[str] = None
    psychological_anxiety: Optional[bool] = None
    onboarding_risk_level: Optional[int] = None


@dataclass
class FloodDetail:
    impact_id: int
    flood_level: str
    water_drain_status: str
    damage_house: bool = False
    damage_vehicle: bool = False
    electric_problem: bool = False
    water_problem: bool = False


@dataclass
class TyphoonDetail:
    impact_id: int
    roof_damage: bool = False
    window_damage: bool = False
    structure_damage: bool = False
    vehicle_damage: bool = False
    electric_problem: bool = False
    water_problem: bool = False


@dataclass
class EarthquakeDetail:
    impact_id: int
    aftershock_feeling: str = "NONE"
    building_crack: bool = False
    house_damage: bool = False
    vehicle_damage: bool = False
    electric_problem: bool = False
    water_problem: bool = False


@dataclass
class FireDetail:
    impact_id: int
    fire_damage_scope: str
    smoke_inhalation: str
    house_damage: bool = False
    vehicle_damage: bool = False
    electric_problem: bool = False
    water_problem: bool = False
    soot_damage: bool = False
    debris_exist: bool = False


@dataclass
class DisasterImpactFull:
    """Gemini 프롬프트 생성 등 세부 정보가 필요한 경우 사용."""
    impact: DisasterImpact
    flood_detail: Optional[FloodDetail] = None
    typhoon_detail: Optional[TyphoonDetail] = None
    earthquake_detail: Optional[EarthquakeDetail] = None
    fire_detail: Optional[FireDetail] = None
