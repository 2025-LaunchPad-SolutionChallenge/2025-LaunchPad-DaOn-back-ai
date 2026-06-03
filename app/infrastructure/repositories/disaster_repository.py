from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.domain.disaster.entity import (
    DisasterImpact,
    DisasterImpactFull,
    EarthquakeDetail,
    FireDetail,
    FloodDetail,
    TyphoonDetail,
)
from app.domain.disaster.repository import DisasterRepository
from app.infrastructure.models.disaster_model import (
    DisasterImpactModel,
    EarthquakeImpactModel,
    FireImpactModel,
    FloodImpactModel,
    TyphoonImpactModel,
)


def _model_to_entity(model: DisasterImpactModel) -> DisasterImpact:
    return DisasterImpact(
        impact_id=model.impact_id,
        user_disaster_id=model.user_disaster_id,
        safety_status=model.safety_status.value if model.safety_status else None,
        residence_status=model.residence_status.value,
        injury_level=model.injury_level.value,
        can_go_out=model.can_go_out,
        available_time=model.available_time.value if model.available_time else None,
        psychological_anxiety=model.psychological_anxiety,
        onboarding_risk_level=model.onboarding_risk_level,
    )


def _model_to_full(model: DisasterImpactModel) -> DisasterImpactFull:
    flood = None
    if model.flood_detail:
        f = model.flood_detail
        flood = FloodDetail(
            impact_id=f.impact_id,
            flood_level=f.flood_level.value,
            water_drain_status=f.water_drain_status.value,
            damage_house=f.damage_house,
            damage_vehicle=f.damage_vehicle,
            electric_problem=f.electric_problem,
            water_problem=f.water_problem,
        )

    typhoon = None
    if model.typhoon_detail:
        t = model.typhoon_detail
        typhoon = TyphoonDetail(
            impact_id=t.impact_id,
            roof_damage=t.roof_damage,
            window_damage=t.window_damage,
            structure_damage=t.structure_damage,
            vehicle_damage=t.vehicle_damage,
            electric_problem=t.electric_problem,
            water_problem=t.water_problem,
        )

    earthquake = None
    if model.earthquake_detail:
        e = model.earthquake_detail
        earthquake = EarthquakeDetail(
            impact_id=e.impact_id,
            aftershock_feeling=e.aftershock_feeling.value,
            building_crack=e.building_crack,
            house_damage=e.house_damage,
            vehicle_damage=e.vehicle_damage,
            electric_problem=e.electric_problem,
            water_problem=e.water_problem,
        )

    fire = None
    if model.fire_detail:
        fi = model.fire_detail
        fire = FireDetail(
            impact_id=fi.impact_id,
            fire_damage_scope=fi.fire_damage_scope.value,
            smoke_inhalation=fi.smoke_inhalation.value,
            house_damage=fi.house_damage,
            vehicle_damage=fi.vehicle_damage,
            electric_problem=fi.electric_problem,
            water_problem=fi.water_problem,
            soot_damage=fi.soot_damage,
            debris_exist=fi.debris_exist,
        )

    return DisasterImpactFull(
        impact=_model_to_entity(model),
        flood_detail=flood,
        typhoon_detail=typhoon,
        earthquake_detail=earthquake,
        fire_detail=fire,
    )


class SQLDisasterRepository(DisasterRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create_impact(self, impact: DisasterImpact) -> DisasterImpact:
        model = DisasterImpactModel(
            user_disaster_id=impact.user_disaster_id,
            safety_status=impact.safety_status,
            residence_status=impact.residence_status,
            injury_level=impact.injury_level,
            psychological_anxiety=impact.psychological_anxiety,
            onboarding_risk_level=impact.onboarding_risk_level,
        )
        self._session.add(model)
        await self._session.flush()
        await self._session.refresh(model)
        return _model_to_entity(model)

    async def create_flood_detail(self, detail: FloodDetail) -> None:
        self._session.add(FloodImpactModel(**detail.__dict__))
        await self._session.flush()

    async def create_typhoon_detail(self, detail: TyphoonDetail) -> None:
        self._session.add(TyphoonImpactModel(**detail.__dict__))
        await self._session.flush()

    async def create_earthquake_detail(self, detail: EarthquakeDetail) -> None:
        self._session.add(EarthquakeImpactModel(**detail.__dict__))
        await self._session.flush()

    async def create_fire_detail(self, detail: FireDetail) -> None:
        self._session.add(FireImpactModel(**detail.__dict__))
        await self._session.flush()

    async def update_context(
        self, user_disaster_id: int, can_go_out: bool, available_time: str
    ) -> Optional[DisasterImpact]:
        result = await self._session.execute(
            select(DisasterImpactModel).where(
                DisasterImpactModel.user_disaster_id == user_disaster_id
            )
        )
        model = result.scalar_one_or_none()
        if model is None:
            return None
        model.can_go_out = can_go_out
        model.available_time = available_time
        await self._session.flush()
        await self._session.refresh(model)
        return _model_to_entity(model)

    async def get_impact_full(
        self, user_disaster_id: int
    ) -> Optional[DisasterImpactFull]:
        result = await self._session.execute(
            select(DisasterImpactModel)
            .where(DisasterImpactModel.user_disaster_id == user_disaster_id)
            .options(
                selectinload(DisasterImpactModel.flood_detail),
                selectinload(DisasterImpactModel.typhoon_detail),
                selectinload(DisasterImpactModel.earthquake_detail),
                selectinload(DisasterImpactModel.fire_detail),
            )
        )
        model = result.scalar_one_or_none()
        return _model_to_full(model) if model else None
