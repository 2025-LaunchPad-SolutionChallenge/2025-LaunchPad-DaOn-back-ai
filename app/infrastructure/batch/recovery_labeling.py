"""매일 자정 실행: 모든 활성 재난에 대해 RecoveryFeatures를 계산하고 회복 단계를 라벨링한다."""

from datetime import date, timedelta
from typing import List, Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import AsyncSessionLocal
from app.domain.recovery.entity import RecoveryFeatures, Stage
from app.domain.recovery.service import label_recovery_stage, _compute_raw_stage
from app.infrastructure.models.checklist_model import ChecklistItemModel
from app.infrastructure.models.disaster_model import (
    DisasterImpactModel,
    RegistrationStatus,
    UserDisasterModel,
)
from app.infrastructure.models.recovery_model import (
    DailyStatusCheckModel,
    RecoveryFeatureModel,
    RecoveryOutputModel,
)

# ── 단계별 기본 추천 할 일 ─────────────────────────────────────────────────
_DEFAULT_TASKS: dict[Stage, list[str]] = {
    Stage.CHAOS: [
        "가족·지인에게 안전 여부 연락하기",
        "가장 가까운 지원 기관(주민센터·적십자) 위치 확인하기",
        "긴급 식수 및 비상식량 점검하기",
    ],
    Stage.STAGNANT: [
        "오늘 할 수 있는 작은 일 하나만 골라 해보기",
        "가까운 사람과 10분 대화하기",
        "집 안 한 곳만 정리해보기",
    ],
    Stage.ATTEMPTING: [
        "체크리스트 항목 중 가장 쉬운 것부터 완료하기",
        "30분 이내 가벼운 외출 시도하기",
        "피해 복구 관련 서류 하나 챙겨두기",
    ],
    Stage.STABLE: [
        "일상 루틴 하나 다시 시작하기 (운동, 요리 등)",
        "장기 복구 계획 한 가지 작성하기",
        "지역 사회 활동 참여해보기",
    ],
    Stage.RECOVERY_MAINTAINED: [
        "이번 주 목표 3가지 세우기",
        "주변 이웃 중 도움이 필요한 분께 연락하기",
        "재난 대비 키트 점검 및 보충하기",
    ],
}


async def run_recovery_labeling_batch() -> None:
    """배치 진입점 — 자체 세션을 생성해 실행한다."""
    async with AsyncSessionLocal() as session:
        try:
            await _run(session)
            await session.commit()
        except Exception as e:
            await session.rollback()
            print(f"[RecoveryBatch] 전체 실패: {e}")
            raise


async def _run(session: AsyncSession) -> None:
    today = date.today()

    result = await session.execute(
        select(UserDisasterModel).where(
            UserDisasterModel.registration_status == RegistrationStatus.ACTIVE
        )
    )
    user_disasters = result.scalars().all()

    for ud in user_disasters:
        try:
            await _process(session, ud, today)
        except Exception as e:
            print(f"[RecoveryBatch] user_disaster={ud.user_disaster_id} 실패: {e}")


async def _process(session: AsyncSession, ud: UserDisasterModel, today: date) -> None:
    uid = ud.user_disaster_id

    # 온보딩 위험도
    impact_row = await session.execute(
        select(DisasterImpactModel).where(DisasterImpactModel.user_disaster_id == uid)
    )
    impact = impact_row.scalar_one_or_none()
    risk_level: int = (impact.onboarding_risk_level or 1) if impact else 1

    # 경과 일수
    days_since = (today - ud.registered_at.date()).days

    # 최근 7일 상태 체크 데이터
    seven_ago = today - timedelta(days=7)
    checks = await _fetch_checks(session, uid, seven_ago, today)
    today_check = next((c for c in checks if c.check_date == today), None)
    last_3 = [c for c in checks if c.check_date >= today - timedelta(days=3)]

    # 7일 피처 계산
    n = len(checks) or 1
    avg_status = sum(
        c.emotion_score + c.condition_score + c.action_score + c.change_score + c.need_score
        for c in checks
    ) / n
    avg_action = sum(c.action_score for c in checks) / n
    outing_cap = sum(1 for c in checks if c.can_go_out) / n
    avg_avail = sum(c.available_time for c in checks) / n

    # 체크리스트 달성률
    completion_rate = await _compute_completion_rate(session, uid, seven_ago, today)

    # 최근 3일 집계
    recent_3d_need = sum(1 for c in last_3 if c.need_score == -1.0)
    recent_3d_no_out = sum(1 for c in last_3 if not c.can_go_out)

    # 현재 단계 + 전이 이력
    current_stage, consec_upper, consec_lower = await _get_stage_and_consecutive(
        session, uid, risk_level
    )

    # 2일 연속 위기 신호
    recent_2d_crisis = await _check_crisis(session, uid, today)

    # 오늘 완료 체크리스트 수
    today_completions = await _count_completions(session, uid, today)

    # 최근 14일 안정성
    fourteen_ago = today - timedelta(days=14)
    outputs_14 = await _fetch_outputs(session, uid, fourteen_ago, today)
    below_stable = any(
        Stage.from_db_str(o.raw_stage) < Stage.STABLE for o in outputs_14
    )
    missing_14 = 14 - len([c for c in checks if c.check_date >= fourteen_ago])

    features = RecoveryFeatures(
        avg_7d_status_score=avg_status,
        avg_7d_action_score=avg_action,
        avg_7d_task_completion_rate=completion_rate,
        outing_capability=outing_cap,
        avg_7d_available_time=avg_avail,
        recent_3d_need_count=recent_3d_need,
        recent_3d_no_outing_count=recent_3d_no_out,
        onboarding_risk_level=risk_level,
        days_since_disaster=days_since,
        current_stage=current_stage,
        consecutive_qualifying_days=consec_upper,
        consecutive_lower_days=consec_lower,
        recent_2d_crisis=recent_2d_crisis,
        today_need_score=today_check.need_score if today_check else 0.0,
        today_completions=today_completions,
        today_can_go_out=today_check.can_go_out if today_check else False,
        recent_14d_below_stable=below_stable,
        missing_days_last_14d=max(0, missing_14),
    )

    new_stage = label_recovery_stage(features)
    raw_stage = _compute_raw_stage(features)
    tasks = _DEFAULT_TASKS[new_stage]

    # RecoveryFeatureModel 저장
    session.add(RecoveryFeatureModel(
        user_disaster_id=uid,
        feature_date=today,
        onboarding_risk_level=risk_level,
        avg_7d_status_score=avg_status,
        avg_7d_action_score=avg_action,
        outing_capability=outing_cap,
        avg_7d_task_completion_rate=completion_rate,
        avg_7d_available_time=avg_avail,
        recent_3d_need_count=recent_3d_need,
        recent_3d_no_outing_count=recent_3d_no_out,
    ))

    # RecoveryOutputModel upsert
    existing = (await session.execute(
        select(RecoveryOutputModel).where(
            RecoveryOutputModel.user_disaster_id == uid,
            RecoveryOutputModel.state_date == today,
        )
    )).scalar_one_or_none()

    stage_str = new_stage.to_db_str()
    raw_str = raw_stage.to_db_str()

    if existing:
        existing.predicted_stage = stage_str
        existing.raw_stage = raw_str
        existing.task_1, existing.task_2, existing.task_3 = tasks
    else:
        session.add(RecoveryOutputModel(
            user_disaster_id=uid,
            state_date=today,
            predicted_stage=stage_str,
            raw_stage=raw_str,
            task_1=tasks[0],
            task_2=tasks[1],
            task_3=tasks[2],
        ))

    await session.flush()


# ── 헬퍼 함수들 ────────────────────────────────────────────────────────────

async def _fetch_checks(
    session: AsyncSession, uid: int, start: date, end: date
) -> List[DailyStatusCheckModel]:
    result = await session.execute(
        select(DailyStatusCheckModel)
        .where(
            DailyStatusCheckModel.user_disaster_id == uid,
            DailyStatusCheckModel.check_date >= start,
            DailyStatusCheckModel.check_date <= end,
        )
        .order_by(DailyStatusCheckModel.check_date.desc())
    )
    return result.scalars().all()


async def _fetch_outputs(
    session: AsyncSession, uid: int, start: date, end: date
) -> List[RecoveryOutputModel]:
    result = await session.execute(
        select(RecoveryOutputModel)
        .where(
            RecoveryOutputModel.user_disaster_id == uid,
            RecoveryOutputModel.state_date >= start,
            RecoveryOutputModel.state_date <= end,
        )
        .order_by(RecoveryOutputModel.state_date.desc())
    )
    return result.scalars().all()


async def _compute_completion_rate(
    session: AsyncSession, uid: int, start: date, end: date
) -> float:
    total_result = await session.execute(
        select(func.count()).where(
            ChecklistItemModel.user_disaster_id == uid,
            ChecklistItemModel.checklist_date >= start,
            ChecklistItemModel.checklist_date <= end,
        )
    )
    total = total_result.scalar() or 0
    if total == 0:
        return 0.0

    done_result = await session.execute(
        select(func.count()).where(
            ChecklistItemModel.user_disaster_id == uid,
            ChecklistItemModel.checklist_date >= start,
            ChecklistItemModel.checklist_date <= end,
            ChecklistItemModel.is_completed == True,
        )
    )
    done = done_result.scalar() or 0
    return done / total


async def _count_completions(session: AsyncSession, uid: int, today: date) -> int:
    result = await session.execute(
        select(func.count()).where(
            ChecklistItemModel.user_disaster_id == uid,
            ChecklistItemModel.checklist_date == today,
            ChecklistItemModel.is_completed == True,
        )
    )
    return result.scalar() or 0


async def _check_crisis(session: AsyncSession, uid: int, today: date) -> bool:
    """2일 연속 외출 불가 AND 체크리스트 완료 0개."""
    two_ago = today - timedelta(days=2)
    checks = await _fetch_checks(session, uid, two_ago, today - timedelta(days=1))
    if len(checks) < 2:
        return False
    for c in checks[:2]:
        completions = await _count_completions(session, uid, c.check_date)
        if c.can_go_out or completions > 0:
            return False
    return True


async def _get_current_stage(
    session: AsyncSession, uid: int, risk_level: int
) -> Stage:
    result = await session.execute(
        select(RecoveryOutputModel)
        .where(RecoveryOutputModel.user_disaster_id == uid)
        .order_by(RecoveryOutputModel.state_date.desc())
        .limit(1)
    )
    last = result.scalar_one_or_none()
    if last:
        return Stage.from_db_str(last.predicted_stage)
    return Stage.CHAOS if risk_level == 3 else Stage.STAGNANT


async def _get_stage_and_consecutive(
    session: AsyncSession, uid: int, risk_level: int
) -> tuple[Stage, int, int]:
    """현재 단계, 연속 상승 일수, 연속 하락 일수를 반환한다."""
    current = await _get_current_stage(session, uid, risk_level)

    # 최근 7일 raw_stage 이력 조회
    result = await session.execute(
        select(RecoveryOutputModel)
        .where(RecoveryOutputModel.user_disaster_id == uid)
        .order_by(RecoveryOutputModel.state_date.desc())
        .limit(7)
    )
    history = result.scalars().all()

    consec_upper = 0
    for row in history:
        raw = Stage.from_db_str(row.raw_stage)
        if raw > current:
            consec_upper += 1
        else:
            break

    consec_lower = 0
    for row in history:
        raw = Stage.from_db_str(row.raw_stage)
        if raw < current:
            consec_lower += 1
        else:
            break

    return current, consec_upper, consec_lower
