from datetime import date
from typing import Optional

from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.domain.home.entity import DailyStatusCheck, HomeSummary, TodayTask
from app.domain.home.repository import HomeRepository
from app.infrastructure.models.checklist_model import ChecklistItemModel
from app.infrastructure.models.disaster_model import DisasterTypeModel
from app.infrastructure.models.disaster_model import UserDisasterModel
from app.infrastructure.models.disaster_model import RegistrationStatus
from app.infrastructure.models.recovery_model import DailyStatusCheckModel
from app.infrastructure.models.recovery_model import RecoveryStageMasterModel
from app.infrastructure.models.user_model import UserModel


def _model_to_entity(model: DailyStatusCheckModel) -> DailyStatusCheck:
    return DailyStatusCheck(
        daily_check_id=model.daily_check_id,
        user_disaster_id=model.user_disaster_id,
        check_date=model.check_date,
        emotion_score=model.emotion_score,
        condition_score=model.condition_score,
        action_score=model.action_score,
        change_score=model.change_score,
        need_score=model.need_score,
        available_time=model.available_time,
        can_go_out=model.can_go_out,
    )


class SQLHomeRepository(HomeRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_user_disaster_id(self, firebase_uid: str) -> Optional[int]:
        result = await self._session.execute(
            select(UserModel)
            .where(UserModel.firebase_uid == firebase_uid)
            .options(selectinload(UserModel.setting))
        )
        user = result.scalar_one_or_none()
        if user is None or user.setting is None:
            return None
        return user.setting.user_disaster_id

    async def exists_today(self, user_disaster_id: int, check_date: date) -> bool:
        result = await self._session.execute(
            select(DailyStatusCheckModel).where(
                DailyStatusCheckModel.user_disaster_id == user_disaster_id,
                DailyStatusCheckModel.check_date == check_date,
            )
        )
        return result.scalar_one_or_none() is not None

    async def save_daily_check(self, check: DailyStatusCheck) -> DailyStatusCheck:
        model = DailyStatusCheckModel(
            user_disaster_id=check.user_disaster_id,
            check_date=check.check_date,
            emotion_score=check.emotion_score,
            condition_score=check.condition_score,
            action_score=check.action_score,
            change_score=check.change_score,
            need_score=check.need_score,
            available_time=check.available_time,
            can_go_out=check.can_go_out,
        )
        self._session.add(model)
        await self._session.flush()
        await self._session.refresh(model)
        return _model_to_entity(model)

    async def update_recovery_progress(
        self, user_disaster_id: int, total_score: int
    ) -> None:
        result = await self._session.execute(
            select(UserDisasterModel).where(
                UserDisasterModel.user_disaster_id == user_disaster_id
            )
        )
        user_disaster = result.scalar_one_or_none()
        if user_disaster is None:
            return
        delta = total_score * 0.02
        user_disaster.recovery_progress = max(
            0.0, min(1.0, user_disaster.recovery_progress + delta)
        )
        await self._session.flush()

    async def get_active_user_disaster_id(self, user_id: int) -> Optional[int]:
        result = await self._session.execute(
            select(UserDisasterModel.user_disaster_id).where(
                UserDisasterModel.user_id == user_id,
                UserDisasterModel.registration_status == RegistrationStatus.ACTIVE,
            ).order_by(UserDisasterModel.registered_at.desc()).limit(1)
        )
        return result.scalar_one_or_none()

    async def get_home_summary(self, user_id: int) -> Optional[HomeSummary]:
        active_disaster_result = await self._session.execute(
            select(
                UserDisasterModel,
                RecoveryStageMasterModel,
                DisasterTypeModel.disaster_name,
                UserModel.name,
            )
            .join(
                RecoveryStageMasterModel,
                RecoveryStageMasterModel.recovery_stage_id
                == UserDisasterModel.recovery_stage_id,
            )
            .join(
                DisasterTypeModel,
                DisasterTypeModel.disaster_type_id == UserDisasterModel.disaster_type_id,
            )
            .join(UserModel, UserModel.user_id == UserDisasterModel.user_id)
            .where(
                UserDisasterModel.user_id == user_id,
                UserDisasterModel.registration_status == RegistrationStatus.ACTIVE,
            )
            .order_by(UserDisasterModel.registered_at.desc())
            .limit(1)
        )
        row = active_disaster_result.first()
        if row is None:
            return None
        user_disaster, stage, disaster_type_name, user_name = row
        today = date.today()

        checklist_count_result = await self._session.execute(
            select(
                func.count(ChecklistItemModel.checklist_item_id),
                func.sum(case((ChecklistItemModel.is_completed.is_(True), 1), else_=0)),
            ).where(
                ChecklistItemModel.user_disaster_id == user_disaster.user_disaster_id,
                ChecklistItemModel.checklist_date == today,
            )
        )
        total_tasks, completed_tasks = checklist_count_result.one()
        today_total_tasks = int(total_tasks or 0)
        today_completed_tasks = int(completed_tasks or 0)

        status_result = await self._session.execute(
            select(DailyStatusCheckModel.daily_check_id).where(
                DailyStatusCheckModel.user_disaster_id == user_disaster.user_disaster_id,
                DailyStatusCheckModel.check_date == today,
            )
        )
        has_daily_status = status_result.scalar_one_or_none() is not None

        return HomeSummary(
            user_disaster_id=int(user_disaster.user_disaster_id),
            user_name=user_name,
            disaster_title=user_disaster.title,
            disaster_type_name=disaster_type_name,
            occurred_at=user_disaster.registered_at,
            recovery_stage_name=stage.stage_name,
            recovery_progress=float(user_disaster.recovery_progress),
            today_total_tasks=today_total_tasks,
            today_completed_tasks=today_completed_tasks,
            daily_status_checked=has_daily_status,
        )

    async def get_today_tasks(
        self,
        *,
        user_disaster_id: int,
        today: date,
        limit: Optional[int] = None,
    ) -> list[TodayTask]:
        stmt = (
            select(ChecklistItemModel)
            .where(
                ChecklistItemModel.user_disaster_id == user_disaster_id,
                ChecklistItemModel.checklist_date == today,
            )
            .order_by(
                ChecklistItemModel.is_completed.asc(),
                ChecklistItemModel.priority.asc(),
                ChecklistItemModel.checklist_item_id.asc(),
            )
        )
        if limit is not None:
            stmt = stmt.limit(limit)

        result = await self._session.execute(stmt)
        rows = result.scalars().all()
        return [
            TodayTask(
                checklist_item_id=int(row.checklist_item_id),
                title=row.title,
                priority=int(row.priority),
                is_completed=bool(row.is_completed),
                is_ai_generated=row.item_source_type == "AI_GENERATED",
            )
            for row in rows
        ]

    async def get_today_status(self, user_disaster_id: int, today: date) -> Optional[DailyStatusCheck]:
        result = await self._session.execute(
            select(DailyStatusCheckModel).where(
                DailyStatusCheckModel.user_disaster_id == user_disaster_id,
                DailyStatusCheckModel.check_date == today,
            )
        )
        model = result.scalar_one_or_none()
        if model is None:
            return None
        return _model_to_entity(model)
