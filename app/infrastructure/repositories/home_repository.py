from datetime import date
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.domain.home.entity import DailyStatusCheck
from app.domain.home.repository import HomeRepository
from app.infrastructure.models.disaster_model import UserDisasterModel
from app.infrastructure.models.recovery_model import DailyStatusCheckModel
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
