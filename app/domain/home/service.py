from datetime import date

from app.common.exceptions import ConflictException, NotFoundException
from app.domain.home.entity import DailyStatusCheck, HomeSummary, TodayTask
from app.domain.home.repository import HomeRepository


async def submit_daily_status(
    repo: HomeRepository,
    firebase_uid: str,
    emotion_score: int,
    condition_score: int,
    action_score: float,
    change_score: int,
    need_score: float,
) -> DailyStatusCheck:
    user_disaster_id = await repo.get_user_disaster_id(firebase_uid)
    if user_disaster_id is None:
        raise NotFoundException("활성화된 재난 정보가 없습니다.")

    today = date.today()
    if await repo.exists_today(user_disaster_id, today):
        raise ConflictException("오늘 이미 상태 체크를 완료했습니다.")

    check = DailyStatusCheck(
        user_disaster_id=user_disaster_id,
        check_date=today,
        emotion_score=emotion_score,
        condition_score=condition_score,
        action_score=action_score,
        change_score=change_score,
        need_score=need_score,
    )
    saved = await repo.save_daily_check(check)
    await repo.update_recovery_progress(user_disaster_id, saved.total_score)
    return saved


async def get_today_daily_status(
    repo: HomeRepository,
    *,
    user_id: int,
) -> DailyStatusCheck | None:
    user_disaster_id = await repo.get_active_user_disaster_id(user_id)
    if user_disaster_id is None:
        raise NotFoundException("활성화된 재난 정보가 없습니다.")
    return await repo.get_today_status(user_disaster_id, date.today())


async def get_home_summary(
    repo: HomeRepository,
    *,
    user_id: int,
) -> HomeSummary:
    summary = await repo.get_home_summary(user_id)
    if summary is None:
        raise NotFoundException("활성화된 재난 정보가 없습니다.")
    return summary


async def get_today_tasks_preview(
    repo: HomeRepository,
    *,
    user_id: int,
) -> list[TodayTask]:
    user_disaster_id = await repo.get_active_user_disaster_id(user_id)
    if user_disaster_id is None:
        raise NotFoundException("활성화된 재난 정보가 없습니다.")
    return await repo.get_today_tasks(
        user_disaster_id=user_disaster_id,
        today=date.today(),
        limit=3,
    )


async def get_today_tasks_full(
    repo: HomeRepository,
    *,
    user_id: int,
) -> list[TodayTask]:
    user_disaster_id = await repo.get_active_user_disaster_id(user_id)
    if user_disaster_id is None:
        raise NotFoundException("활성화된 재난 정보가 없습니다.")
    return await repo.get_today_tasks(
        user_disaster_id=user_disaster_id,
        today=date.today(),
        limit=None,
    )
