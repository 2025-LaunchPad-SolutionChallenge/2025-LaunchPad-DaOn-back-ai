from __future__ import annotations

from datetime import date, datetime
from typing import Any

from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.common.exceptions import AppException
from app.domain.disaster.entity import (
    DisasterDetail,
    DisasterListItem,
    DisasterListPage,
    DisasterTypeSnapshot,
    ImpactSnapshot,
    RecoveryStageSnapshot,
)
from app.domain.disaster.repository import DisasterRepository
from app.domain.recovery.service import calculate_onboarding_risk_level
from app.infrastructure.models.disaster_model import (
    AftershockFeeling,
    DisasterTypeModel,
    AvailableTime,
    DisasterImpactModel,
    EarthquakeImpactModel,
    FireDamageScope,
    FireImpactModel,
    FloodImpactModel,
    FloodLevel,
    InjuryLevel,
    RegistrationStatus,
    ResidenceStatus,
    SafetyStatus,
    SmokeInhalation,
    TyphoonImpactModel,
    UserDisasterModel,
    WaterDrainStatus,
)
from app.infrastructure.models.recovery_model import RecoveryFeatureModel, RecoveryOutputModel, RecoveryStageMasterModel
from app.infrastructure.models.user_model import UserSettingModel


def _to_impact_snapshot(impact: DisasterImpactModel | None) -> ImpactSnapshot | None:
    if impact is None:
        return None
    return ImpactSnapshot(
        safety_status=impact.safety_status.value if impact.safety_status else None,
        residence_status=impact.residence_status.value if impact.residence_status else None,
        injury_level=impact.injury_level.value if impact.injury_level else None,
        psychological_anxiety=impact.psychological_anxiety,
        can_go_out=impact.can_go_out,
        available_time=impact.available_time.value if impact.available_time else None,
    )


def _to_detail_payload(row: UserDisasterModel) -> dict[str, Any] | None:
    impact = row.impact
    if impact is None:
        return None
    disaster_code = row.disaster_type.disaster_code
    if disaster_code == "FLOOD" and impact.flood_detail:
        d = impact.flood_detail
        return {
            "floodLevel": d.flood_level.value,
            "waterDrainStatus": d.water_drain_status.value,
            "damageHouse": d.damage_house,
            "damageVehicle": d.damage_vehicle,
            "electricProblem": d.electric_problem,
            "waterProblem": d.water_problem,
        }
    if disaster_code == "EARTHQUAKE" and impact.earthquake_detail:
        d = impact.earthquake_detail
        return {
            "aftershockFeeling": d.aftershock_feeling.value,
            "buildingCrack": d.building_crack,
            "houseDamage": d.house_damage,
            "vehicleDamage": d.vehicle_damage,
            "electricProblem": d.electric_problem,
            "waterProblem": d.water_problem,
        }
    if disaster_code == "TYPHOON" and impact.typhoon_detail:
        d = impact.typhoon_detail
        return {
            "roofDamage": d.roof_damage,
            "windowDamage": d.window_damage,
            "structureDamage": d.structure_damage,
            "vehicleDamage": d.vehicle_damage,
            "electricProblem": d.electric_problem,
            "waterProblem": d.water_problem,
        }
    if disaster_code == "FIRE" and impact.fire_detail:
        d = impact.fire_detail
        return {
            "fireDamageScope": d.fire_damage_scope.value,
            "smokeInhalation": d.smoke_inhalation.value,
            "houseDamage": d.house_damage,
            "sootDamage": d.soot_damage,
            "debrisExist": d.debris_exist,
            "vehicleDamage": d.vehicle_damage,
            "electricProblem": d.electric_problem,
            "waterProblem": d.water_problem,
        }
    return None


class SqlAlchemyDisasterRepository(DisasterRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_disasters_page(self, *, user_id: int, page: int, size: int) -> DisasterListPage:
        order_priority = case(
            (UserDisasterModel.registration_status == RegistrationStatus.ACTIVE, 0),
            (UserDisasterModel.registration_status == RegistrationStatus.EXPIRED, 1),
            (UserDisasterModel.registration_status == RegistrationStatus.ARCHIVED, 2),
            else_=3,
        )

        total_result = await self._session.execute(
            select(func.count(UserDisasterModel.user_disaster_id)).where(
                UserDisasterModel.user_id == user_id,
            )
        )
        total_elements = int(total_result.scalar_one() or 0)

        stmt = (
            select(UserDisasterModel)
            .options(
                joinedload(UserDisasterModel.disaster_type),
                joinedload(UserDisasterModel.recovery_stage),
            )
            .where(UserDisasterModel.user_id == user_id)
            .order_by(order_priority, UserDisasterModel.registered_at.desc())
            .offset(page * size)
            .limit(size)
        )
        result = await self._session.execute(stmt)
        rows = result.scalars().all()

        items = [
            DisasterListItem(
                user_disaster_id=row.user_disaster_id,
                title=row.title,
                disaster_type_code=row.disaster_type.disaster_code,
                disaster_type_name=row.disaster_type.disaster_name,
                status=row.registration_status.value,
                occurred_at=row.registered_at,
                ended_at=row.ended_at,
                recovery_stage=RecoveryStageSnapshot(
                    stage_code=row.recovery_stage.stage_code,
                    stage_name=row.recovery_stage.stage_name,
                ),
                recovery_progress=row.recovery_progress,
            )
            for row in rows
        ]
        return DisasterListPage(
            content=items,
            page=page,
            size=size,
            total_elements=total_elements,
        )

    async def get_disaster_detail(self, *, user_id: int, user_disaster_id: int) -> DisasterDetail | None:
        row = await self._get_owned_disaster(user_id=user_id, user_disaster_id=user_disaster_id)
        if row is None:
            return None
        return DisasterDetail(
            user_disaster_id=row.user_disaster_id,
            title=row.title,
            disaster_type=DisasterTypeSnapshot(
                disaster_type_id=row.disaster_type.disaster_type_id,
                disaster_code=row.disaster_type.disaster_code,
                name=row.disaster_type.disaster_name,
            ),
            status=row.registration_status.value,
            occurred_at=row.registered_at,
            ended_at=row.ended_at,
            recovery_stage=RecoveryStageSnapshot(
                stage_code=row.recovery_stage.stage_code,
                stage_name=row.recovery_stage.stage_name,
            ),
            recovery_progress=row.recovery_progress,
            impact=_to_impact_snapshot(row.impact),
            detail=_to_detail_payload(row),
        )

    async def update_disaster(
        self,
        *,
        user_id: int,
        user_disaster_id: int,
        title: str | None = None,
        occurred_at: datetime | None = None,
        impact_updates: dict[str, object] | None = None,
        detail_updates: dict[str, object] | None = None,
    ) -> None:
        row = await self._get_owned_disaster(user_id=user_id, user_disaster_id=user_disaster_id)
        if row is None:
            raise AppException(
                status_code=404,
                code=404,
                message="존재하지 않는 재난입니다.",
                error_key="DISASTER_NOT_FOUND",
            )
        if row.registration_status != RegistrationStatus.ACTIVE:
            raise AppException(
                status_code=409,
                code=409,
                message="ACTIVE 상태의 재난만 수정할 수 있습니다.",
                error_key="DISASTER_NOT_EDITABLE",
            )

        if title is not None:
            row.title = title
        if occurred_at is not None:
            row.registered_at = occurred_at
        if impact_updates:
            impact = self._upsert_impact(row, impact_updates)
            if detail_updates:
                self._upsert_detail(row, impact, detail_updates)
        elif detail_updates:
            impact = self._upsert_impact(row, {})
            self._upsert_detail(row, impact, detail_updates)

        await self._session.flush()

    async def close_disaster(
        self,
        *,
        user_id: int,
        user_disaster_id: int,
        action: str,
        ended_at: datetime | None,
    ) -> tuple[str, datetime]:
        row = await self._get_owned_disaster(user_id=user_id, user_disaster_id=user_disaster_id)
        if row is None:
            raise AppException(
                status_code=404,
                code=404,
                message="존재하지 않는 재난입니다.",
                error_key="DISASTER_NOT_FOUND",
            )
        if row.registration_status != RegistrationStatus.ACTIVE:
            raise AppException(
                status_code=409,
                code=409,
                message="이미 종료되었거나 보관된 재난입니다.",
                error_key="DISASTER_ALREADY_CLOSED",
            )
        resolved_ended_at = ended_at or datetime.utcnow()
        row.ended_at = resolved_ended_at
        row.registration_status = (
            RegistrationStatus.EXPIRED if action == "CLOSE" else RegistrationStatus.ARCHIVED
        )
        await self._session.flush()
        return row.registration_status.value, resolved_ended_at

    async def create_onboarding(
        self,
        *,
        user_id: int,
        disaster_type: str,
        safety_status: str | None,
        residence_status: str,
        injury_level: str,
        damages: list[bool],
        flood_level: str | None,
        water_drain_status: str | None,
        aftershock_feeling: str | None,
        fire_damage_scope: str | None,
        smoke_inhalation: str | None,
    ) -> tuple[int, int, int]:
        type_row_result = await self._session.execute(
            select(DisasterTypeModel).where(DisasterTypeModel.disaster_code == disaster_type)
        )
        type_row = type_row_result.scalar_one_or_none()
        if type_row is None:
            raise AppException(
                status_code=400,
                code=400,
                message="유효하지 않은 disasterType 입니다.",
                error_key="INVALID_DISASTER_TYPE",
            )
        disaster_type_id = type_row.disaster_type_id

        stage_result = await self._session.execute(
            select(RecoveryStageMasterModel)
            .where(RecoveryStageMasterModel.stage_code == "CHAOS")
            .limit(1)
        )
        stage_row = stage_result.scalar_one_or_none()
        if stage_row is None:
            stage_fallback = await self._session.execute(
                select(RecoveryStageMasterModel).order_by(
                    RecoveryStageMasterModel.recovery_stage_id.asc()
                ).limit(1)
            )
            stage_row = stage_fallback.scalar_one_or_none()
        if stage_row is None:
            raise AppException(
                status_code=500,
                code=500,
                message="초기 회복단계 설정이 없습니다.",
                error_key="RECOVERY_STAGE_NOT_CONFIGURED",
            )

        user_disaster = UserDisasterModel(
            user_id=user_id,
            disaster_type_id=int(disaster_type_id),
            disaster_type=type_row,
            recovery_stage_id=int(stage_row.recovery_stage_id),
            recovery_stage=stage_row,
            registration_status=RegistrationStatus.ACTIVE,
            recovery_progress=0.0,
        )
        self._session.add(user_disaster)
        await self._session.flush()

        psych_indices = {"FLOOD": 4, "TYPHOON": 7, "EARTHQUAKE": 6, "FIRE": 5}
        idx = psych_indices.get(disaster_type)
        psychological_anxiety = bool(damages[idx]) if idx is not None and idx < len(damages) else False
        onboarding_risk_level = calculate_onboarding_risk_level(
            ImpactSnapshot(
                safety_status=safety_status,
                residence_status=residence_status,
                injury_level=injury_level,
                psychological_anxiety=psychological_anxiety,
                can_go_out=None,
                available_time=None,
            )
        )
        impact = DisasterImpactModel(
            user_disaster_id=user_disaster.user_disaster_id,
            safety_status=SafetyStatus(str(safety_status)) if safety_status else None,
            residence_status=ResidenceStatus(str(residence_status)),
            injury_level=InjuryLevel(str(injury_level)),
            psychological_anxiety=psychological_anxiety,
            onboarding_risk_level=onboarding_risk_level,
        )
        self._session.add(impact)
        await self._session.flush()

        if disaster_type == "FLOOD":
            if flood_level is None or water_drain_status is None:
                raise AppException(
                    status_code=400,
                    code=400,
                    message="홍수 필수 필드 누락 (floodLevel, waterDrainStatus)",
                    error_key="MISSING_REQUIRED_FIELD",
                )
            self._session.add(
                FloodImpactModel(
                    impact_id=impact.impact_id,
                    flood_level=FloodLevel(str(flood_level)),
                    water_drain_status=WaterDrainStatus(str(water_drain_status)),
                    damage_house=bool(damages[0]) if len(damages) > 0 else False,
                    damage_vehicle=bool(damages[1]) if len(damages) > 1 else False,
                    electric_problem=bool(damages[2]) if len(damages) > 2 else False,
                    water_problem=bool(damages[3]) if len(damages) > 3 else False,
                )
            )
        elif disaster_type == "EARTHQUAKE":
            if aftershock_feeling is None:
                raise AppException(
                    status_code=400,
                    code=400,
                    message="지진 필수 필드 누락 (aftershockFeeling)",
                    error_key="MISSING_REQUIRED_FIELD",
                )
            self._session.add(
                EarthquakeImpactModel(
                    impact_id=impact.impact_id,
                    aftershock_feeling=AftershockFeeling(str(aftershock_feeling)),
                    building_crack=bool(damages[0]) if len(damages) > 0 else False,
                    house_damage=bool(damages[1]) if len(damages) > 1 else False,
                    vehicle_damage=bool(damages[2]) if len(damages) > 2 else False,
                    electric_problem=bool(damages[3]) if len(damages) > 3 else False,
                    water_problem=bool(damages[4]) if len(damages) > 4 else False,
                )
            )
        elif disaster_type == "TYPHOON":
            self._session.add(
                TyphoonImpactModel(
                    impact_id=impact.impact_id,
                    roof_damage=bool(damages[0]) if len(damages) > 0 else False,
                    window_damage=bool(damages[1]) if len(damages) > 1 else False,
                    structure_damage=bool(damages[2]) if len(damages) > 2 else False,
                    vehicle_damage=bool(damages[3]) if len(damages) > 3 else False,
                    electric_problem=bool(damages[4]) if len(damages) > 4 else False,
                    water_problem=bool(damages[5]) if len(damages) > 5 else False,
                )
            )
        elif disaster_type == "FIRE":
            if fire_damage_scope is None or smoke_inhalation is None:
                raise AppException(
                    status_code=400,
                    code=400,
                    message="화재 필수 필드 누락 (fireDamageScope, smokeInhalation)",
                    error_key="MISSING_REQUIRED_FIELD",
                )
            self._session.add(
                FireImpactModel(
                    impact_id=impact.impact_id,
                    fire_damage_scope=FireDamageScope(str(fire_damage_scope)),
                    smoke_inhalation=SmokeInhalation(str(smoke_inhalation)),
                    house_damage=bool(damages[0]) if len(damages) > 0 else False,
                    vehicle_damage=bool(damages[1]) if len(damages) > 1 else False,
                    electric_problem=bool(damages[2]) if len(damages) > 2 else False,
                    water_problem=bool(damages[3]) if len(damages) > 3 else False,
                    soot_damage=bool(damages[6]) if len(damages) > 6 else False,
                    debris_exist=bool(damages[7]) if len(damages) > 7 else False,
                )
            )

        setting_result = await self._session.execute(
            select(UserSettingModel).where(UserSettingModel.user_id == user_id)
        )
        setting = setting_result.scalar_one_or_none()
        if setting is None:
            setting = UserSettingModel(
                user_id=user_id,
                allow_push_notification=None,
                user_disaster_id=user_disaster.user_disaster_id,
            )
            self._session.add(setting)
        else:
            setting.user_disaster_id = user_disaster.user_disaster_id

        await self._session.flush()
        return int(user_disaster.user_disaster_id), int(impact.impact_id), int(impact.onboarding_risk_level or 1)

    async def get_recovery_stage_detail(
        self,
        *,
        user_id: int,
        user_disaster_id: int,
    ) -> tuple[int, str, str, str]:
        row = await self._get_owned_disaster(user_id=user_id, user_disaster_id=user_disaster_id)
        if row is None:
            raise AppException(
                status_code=404,
                code=404,
                message="해당 disasterId가 존재하지 않습니다.",
                error_key="DISASTER_NOT_FOUND",
            )
        stage_map = {
            "CHAOS": (1, "CHAOS", "혼란기", "상황을 받아들이는 것만으로도 버거운 상태예요."),
            "STAGNANT": (2, "STAGNANT", "정체기", "조금은 익숙해졌지만, 앞으로 나아가긴 어려운 상태예요."),
            "ATTEMPTING": (3, "ATTEMPTING", "시도기", "조심스럽게 다시 움직이기 시작한 상태예요."),
            "STABLE": (4, "STABLE", "안정기", "일상이 어느 정도 회복되고 있는 상태예요."),
            "RECOVERY_MAINTAINED": (
                5,
                "RECOVERY_MAINTAINED",
                "회복 유지기",
                "회복된 일상을 안정적으로 유지하고 있어요.",
            ),
        }
        output_result = await self._session.execute(
            select(RecoveryOutputModel)
            .where(RecoveryOutputModel.user_disaster_id == user_disaster_id)
            .order_by(RecoveryOutputModel.state_date.desc())
            .limit(1)
        )
        output = output_result.scalar_one_or_none()
        code = output.predicted_stage if output is not None else "CHAOS"
        return stage_map.get(code, stage_map["CHAOS"])

    async def get_recovery_graph_points(
        self,
        *,
        user_id: int,
        user_disaster_id: int,
    ) -> list[tuple[date, float | None, str, str]]:
        row = await self._get_owned_disaster(user_id=user_id, user_disaster_id=user_disaster_id)
        if row is None:
            raise AppException(
                status_code=404,
                code=404,
                message="해당 disasterId가 존재하지 않습니다.",
                error_key="DISASTER_NOT_FOUND",
            )
        _STAGE_NAME = {
            "CHAOS": "혼란기",
            "STAGNANT": "정체기",
            "ATTEMPTING": "시도기",
            "STABLE": "안정기",
            "RECOVERY_MAINTAINED": "회복 유지기",
        }
        _STAGE_BASE = {
            "CHAOS": 0.0,
            "STAGNANT": 20.0,
            "ATTEMPTING": 40.0,
            "STABLE": 60.0,
            "RECOVERY_MAINTAINED": 80.0,
        }
        result = await self._session.execute(
            select(
                RecoveryOutputModel.state_date,
                RecoveryOutputModel.predicted_stage,
                RecoveryFeatureModel.avg_7d_task_completion_rate,
            )
            .outerjoin(
                RecoveryFeatureModel,
                (RecoveryFeatureModel.user_disaster_id == user_disaster_id)
                & (RecoveryFeatureModel.feature_date == RecoveryOutputModel.state_date),
            )
            .where(RecoveryOutputModel.user_disaster_id == user_disaster_id)
            .order_by(RecoveryOutputModel.state_date.asc())
        )
        rows = result.all()
        if not rows:
            return []

        points = []
        for state_date, stage_code, completion_rate in rows:
            base = _STAGE_BASE.get(stage_code)
            if base is not None and completion_rate is not None:
                score = round(base + (completion_rate * 20), 1)
            else:
                score = None
            points.append((state_date, score, stage_code, _STAGE_NAME.get(stage_code, stage_code)))
        return points

    async def get_latest_recovery_progress(
        self,
        *,
        user_id: int,
        user_disaster_id: int,
    ) -> tuple[float | None, str | None, str | None]:
        points = await self.get_recovery_graph_points(
            user_id=user_id,
            user_disaster_id=user_disaster_id,
        )
        if not points:
            return None, None, None
        _, score, stage_code, stage_name = points[-1]
        return score, stage_code, stage_name

    async def _get_owned_disaster(
        self,
        *,
        user_id: int,
        user_disaster_id: int,
    ) -> UserDisasterModel | None:
        result = await self._session.execute(
            select(UserDisasterModel)
            .options(
                joinedload(UserDisasterModel.disaster_type),
                joinedload(UserDisasterModel.recovery_stage),
                joinedload(UserDisasterModel.impact).joinedload(DisasterImpactModel.flood_detail),
                joinedload(UserDisasterModel.impact).joinedload(DisasterImpactModel.earthquake_detail),
                joinedload(UserDisasterModel.impact).joinedload(DisasterImpactModel.typhoon_detail),
                joinedload(UserDisasterModel.impact).joinedload(DisasterImpactModel.fire_detail),
            )
            .where(UserDisasterModel.user_disaster_id == user_disaster_id)
        )
        row = result.scalar_one_or_none()
        if row is None:
            return None
        if row.user_id != user_id:
            raise AppException(
                status_code=403,
                code=403,
                message="본인 재난만 접근할 수 있습니다.",
                error_key="FORBIDDEN",
            )
        return row

    def _upsert_impact(
        self,
        row: UserDisasterModel,
        updates: dict[str, object],
    ) -> DisasterImpactModel:
        impact = row.impact
        if impact is None:
            impact = DisasterImpactModel(
                user_disaster_id=row.user_disaster_id,
                residence_status=ResidenceStatus.LIVABLE,
                injury_level=InjuryLevel.NONE,
            )
            self._session.add(impact)
            row.impact = impact

        if "safety_status" in updates:
            value = updates["safety_status"]
            impact.safety_status = SafetyStatus(str(value)) if value is not None else None
        if "residence_status" in updates and updates["residence_status"] is not None:
            impact.residence_status = ResidenceStatus(str(updates["residence_status"]))
        if "injury_level" in updates and updates["injury_level"] is not None:
            impact.injury_level = InjuryLevel(str(updates["injury_level"]))
        if "can_go_out" in updates:
            value = updates["can_go_out"]
            impact.can_go_out = bool(value) if value is not None else None
        if "available_time" in updates:
            value = updates["available_time"]
            impact.available_time = AvailableTime(str(value)) if value is not None else None
        return impact

    def _upsert_detail(
        self,
        row: UserDisasterModel,
        impact: DisasterImpactModel,
        updates: dict[str, object],
    ) -> None:
        code = row.disaster_type.disaster_code
        if code == "FLOOD":
            detail = impact.flood_detail
            if detail is None:
                detail = FloodImpactModel(
                    impact=impact,
                    flood_level=FloodLevel.NONE,
                    water_drain_status=WaterDrainStatus.STILL_PRESENT,
                    damage_house=False,
                    damage_vehicle=False,
                    electric_problem=False,
                    water_problem=False,
                )
                self._session.add(detail)
                impact.flood_detail = detail
            if "flood_level" in updates and updates["flood_level"] is not None:
                detail.flood_level = FloodLevel(str(updates["flood_level"]))
            if "water_drain_status" in updates and updates["water_drain_status"] is not None:
                detail.water_drain_status = WaterDrainStatus(str(updates["water_drain_status"]))
            if "damage_house" in updates and updates["damage_house"] is not None:
                detail.damage_house = bool(updates["damage_house"])
            if "damage_vehicle" in updates and updates["damage_vehicle"] is not None:
                detail.damage_vehicle = bool(updates["damage_vehicle"])
            if "electric_problem" in updates and updates["electric_problem"] is not None:
                detail.electric_problem = bool(updates["electric_problem"])
            if "water_problem" in updates and updates["water_problem"] is not None:
                detail.water_problem = bool(updates["water_problem"])
            return

        if code == "EARTHQUAKE":
            detail = impact.earthquake_detail
            if detail is None:
                detail = EarthquakeImpactModel(
                    impact=impact,
                    aftershock_feeling=AftershockFeeling.NONE,
                    building_crack=False,
                    house_damage=False,
                    vehicle_damage=False,
                    electric_problem=False,
                    water_problem=False,
                )
                self._session.add(detail)
                impact.earthquake_detail = detail
            if "aftershock_feeling" in updates and updates["aftershock_feeling"] is not None:
                detail.aftershock_feeling = AftershockFeeling(str(updates["aftershock_feeling"]))
            if "building_crack" in updates and updates["building_crack"] is not None:
                detail.building_crack = bool(updates["building_crack"])
            if "house_damage" in updates and updates["house_damage"] is not None:
                detail.house_damage = bool(updates["house_damage"])
            if "vehicle_damage" in updates and updates["vehicle_damage"] is not None:
                detail.vehicle_damage = bool(updates["vehicle_damage"])
            if "electric_problem" in updates and updates["electric_problem"] is not None:
                detail.electric_problem = bool(updates["electric_problem"])
            if "water_problem" in updates and updates["water_problem"] is not None:
                detail.water_problem = bool(updates["water_problem"])
            return

        if code == "TYPHOON":
            detail = impact.typhoon_detail
            if detail is None:
                detail = TyphoonImpactModel(
                    impact=impact,
                    roof_damage=False,
                    window_damage=False,
                    structure_damage=False,
                    vehicle_damage=False,
                    electric_problem=False,
                    water_problem=False,
                )
                self._session.add(detail)
                impact.typhoon_detail = detail
            for field in (
                "roof_damage",
                "window_damage",
                "structure_damage",
                "vehicle_damage",
                "electric_problem",
                "water_problem",
            ):
                if field in updates and updates[field] is not None:
                    setattr(detail, field, bool(updates[field]))
            return

        if code == "FIRE":
            detail = impact.fire_detail
            if detail is None:
                detail = FireImpactModel(
                    impact=impact,
                    fire_damage_scope=FireDamageScope.SMOKE_ONLY,
                    smoke_inhalation=SmokeInhalation.NONE,
                    house_damage=False,
                    soot_damage=False,
                    debris_exist=False,
                    vehicle_damage=False,
                    electric_problem=False,
                    water_problem=False,
                )
                self._session.add(detail)
                impact.fire_detail = detail
            if "fire_damage_scope" in updates and updates["fire_damage_scope"] is not None:
                detail.fire_damage_scope = FireDamageScope(str(updates["fire_damage_scope"]))
            if "smoke_inhalation" in updates and updates["smoke_inhalation"] is not None:
                detail.smoke_inhalation = SmokeInhalation(str(updates["smoke_inhalation"]))
            for field in (
                "house_damage",
                "soot_damage",
                "debris_exist",
                "vehicle_damage",
                "electric_problem",
                "water_problem",
            ):
                if field in updates and updates[field] is not None:
                    setattr(detail, field, bool(updates[field]))
