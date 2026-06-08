from datetime import date

from app.common.exceptions import ConflictException, NotFoundException
from app.domain.home.entity import DailyStatusCheck
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
