from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.dependencies import get_db
from app.common.dependencies import get_current_user
from app.common.swagger import error_responses
from app.domain.home import service as home_service
from app.infrastructure.repositories.home_repository import SQLHomeRepository
from app.interface.home.schema import (
    DailyStatusLookupResponse,
    DailyStatusRequest,
    DailyStatusResponse,
    HomeSummaryResponse,
    TodayTaskItemResponse,
    TodayTasksResponse,
)

router = APIRouter(prefix="/home", tags=["home"])


@router.post(
    "/daily-status",
    response_model=DailyStatusResponse,
    summary="일일 상태 체크 제출",
    description=(
        "감정/에너지/활동/회복/필요 점수를 저장하고, "
        "당일 체크 중복 여부를 검증한 뒤 총점을 계산해 반환합니다."
    ),
    responses=error_responses(400, 401, 403, 404, 409, 500),
)
async def submit_daily_status(
    req: DailyStatusRequest,
    db: AsyncSession = Depends(get_db),
    current_user: dict[str, Any] = Depends(get_current_user),
) -> DailyStatusResponse:
    repo = SQLHomeRepository(db)
    saved = await home_service.submit_daily_status(
        repo=repo,
        firebase_uid=current_user["firebase_uid"],
        emotion_score=req.emotion_score,
        condition_score=req.energy_score,
        action_score=req.activity_score,
        change_score=req.recovery_score,
        need_score=req.need_score,
    )
    return DailyStatusResponse(
        daily_check_id=saved.daily_check_id,
        total_score=saved.total_score,
        message="상태 체크 완료",
    )


@router.get(
    "/daily-status",
    response_model=DailyStatusLookupResponse,
    summary="오늘의 상태 체크 조회",
    description="오늘 상태 체크 완료 여부와 완료 시 입력 점수를 조회합니다.",
    responses=error_responses(401, 404, 500),
)
async def get_daily_status(
    db: AsyncSession = Depends(get_db),
    current_user: dict[str, Any] = Depends(get_current_user),
) -> DailyStatusLookupResponse:
    repo = SQLHomeRepository(db)
    user_id = int(current_user["sub"])
    daily_status = await home_service.get_today_daily_status(repo=repo, user_id=user_id)
    if daily_status is None:
        return DailyStatusLookupResponse(
            checked=False,
            message="오늘 상태 체크가 아직 없습니다.",
        )
    return DailyStatusLookupResponse(
        checked=True,
        daily_check_id=daily_status.daily_check_id,
        emotion_score=daily_status.emotion_score,
        energy_score=daily_status.condition_score,
        activity_score=daily_status.action_score,
        recovery_score=daily_status.change_score,
        need_score=daily_status.need_score,
        total_score=daily_status.total_score,
        message="오늘 상태 체크 조회 완료",
    )


@router.get(
    "/summary",
    response_model=HomeSummaryResponse,
    summary="홈 화면 요약 정보 조회",
    description="활성 재난 기준 회복 단계, 진행률, 오늘 체크/할일 요약 정보를 조회합니다.",
    responses=error_responses(401, 404, 500),
)
async def get_home_summary(
    db: AsyncSession = Depends(get_db),
    current_user: dict[str, Any] = Depends(get_current_user),
) -> HomeSummaryResponse:
    repo = SQLHomeRepository(db)
    user_id = int(current_user["sub"])
    summary = await home_service.get_home_summary(repo=repo, user_id=user_id)
    return HomeSummaryResponse(
        user_disaster_id=summary.user_disaster_id,
        user_name=summary.user_name,
        disaster_title=summary.disaster_title,
        disaster_type_name=summary.disaster_type_name,
        occurred_at=summary.occurred_at.isoformat(),
        recovery_stage_name=summary.recovery_stage_name,
        recovery_progress=summary.recovery_progress,
        daily_status_checked=summary.daily_status_checked,
        today_total_tasks=summary.today_total_tasks,
        today_completed_tasks=summary.today_completed_tasks,
        today_completion_rate=summary.today_completion_rate,
    )


@router.get(
    "/today-tasks",
    response_model=TodayTasksResponse,
    summary="오늘의 할 일 3개 미리보기",
    description="오늘 체크리스트를 우선순위 기준으로 정렬해 상위 3개를 조회합니다.",
    responses=error_responses(401, 404, 500),
)
async def get_today_tasks_preview(
    db: AsyncSession = Depends(get_db),
    current_user: dict[str, Any] = Depends(get_current_user),
) -> TodayTasksResponse:
    repo = SQLHomeRepository(db)
    user_id = int(current_user["sub"])
    tasks = await home_service.get_today_tasks_preview(repo=repo, user_id=user_id)
    return TodayTasksResponse(
        total_count=len(tasks),
        items=[
            TodayTaskItemResponse(
                checklist_item_id=task.checklist_item_id,
                title=task.title,
                priority=task.priority,
                is_completed=task.is_completed,
                is_ai_generated=task.is_ai_generated,
            )
            for task in tasks
        ],
    )


@router.get(
    "/today-tasks/full",
    response_model=TodayTasksResponse,
    summary="오늘의 할 일 전체 보기",
    description="오늘 체크리스트 전체 항목을 조회합니다.",
    responses=error_responses(401, 404, 500),
)
async def get_today_tasks_full(
    db: AsyncSession = Depends(get_db),
    current_user: dict[str, Any] = Depends(get_current_user),
) -> TodayTasksResponse:
    repo = SQLHomeRepository(db)
    user_id = int(current_user["sub"])
    tasks = await home_service.get_today_tasks_full(repo=repo, user_id=user_id)
    return TodayTasksResponse(
        total_count=len(tasks),
        items=[
            TodayTaskItemResponse(
                checklist_item_id=task.checklist_item_id,
                title=task.title,
                priority=task.priority,
                is_completed=task.is_completed,
                is_ai_generated=task.is_ai_generated,
            )
            for task in tasks
        ],
    )
