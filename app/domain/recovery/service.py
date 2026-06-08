from app.domain.disaster.entity import DisasterImpact
from app.domain.recovery.entity import RecoveryFeatures, Stage


# ── 온보딩 위험도 계산 ─────────────────────────────────────────────────────

def calculate_onboarding_risk_level(impact: DisasterImpact) -> int:
    """
    재난 피해 정보를 기반으로 온보딩 위험도(1~3)를 계산한다.
    Max 조건: 하나라도 해당하면 해당 단계로 분류.
    """
    if (
        impact.safety_status == "EMERGENCY"
        or impact.residence_status == "UNLIVABLE"
        or impact.injury_level == "SEVERE"
    ):
        return 3

    if (
        impact.safety_status == "DAMAGED"
        or impact.residence_status == "PARTIAL_DAMAGE"
        or impact.injury_level == "MINOR"
        or impact.psychological_anxiety is True
    ):
        return 2

    return 1


# ── 회복 라벨링 ────────────────────────────────────────────────────────────

def label_recovery_stage(f: RecoveryFeatures) -> Stage:
    """
    전이 규칙을 포함한 최종 회복 단계를 계산한다.
    배치 잡이 매일 자정 RecoveryFeatures를 구성해 이 함수를 호출한다.
    """
    # 1. 즉시 위기 강등: 2일 연속 (외출 불가 AND 달성 0)
    if f.recent_2d_crisis:
        new_stage = Stage(max(Stage.CHAOS, f.current_stage - 1))
        return new_stage

    # 2. 온보딩 강제 혼란기: risk=3 이면 최소 3일 Chaos
    if f.onboarding_risk_level == 3 and f.days_since_disaster < 3:
        return Stage.CHAOS

    # 3. 초기 안정화 상한: 데이터가 충분히 쌓이기 전까지 단계 상한 적용
    stage_cap = _get_stage_cap(f.days_since_disaster)

    # 4. 순수 조건 기반 단계 계산
    raw = _compute_raw_stage(f)
    raw = Stage(min(raw, stage_cap))

    # 5. 정체기 유지 조건: 현재 Stagnant이고 hold 조건 존재 시 상승 차단
    if f.current_stage == Stage.STAGNANT and raw > Stage.STAGNANT:
        if _is_stagnant_held(f):
            raw = Stage.STAGNANT

    # 6. 회복 유지기 안정성 검증
    if raw == Stage.RECOVERY_MAINTAINED:
        if f.recent_14d_below_stable and f.missing_days_last_14d > 2:
            raw = Stage.STABLE

    # 7. 전이 규칙 적용
    return _apply_transition(f, raw)


def _get_stage_cap(days: int) -> Stage:
    """초기 안정화 규칙: 경과 일수에 따른 단계 상한.
    1~3일(days_since 0~2): Chaos/Stagnant만
    4~6일(days_since 3~5): Attempting까지
    7일 이상(days_since 6+): 제한 없음
    """
    if days < 3:
        return Stage.STAGNANT
    if days < 6:
        return Stage.ATTEMPTING
    return Stage.RECOVERY_MAINTAINED


def _compute_raw_stage(f: RecoveryFeatures) -> Stage:
    """전이 규칙 미포함, 오늘 피처만으로 단계를 판정한다."""
    # 회복 유지기
    if (
        f.avg_7d_status_score >= 5
        and f.avg_7d_action_score >= 2.5
        and f.avg_7d_task_completion_rate >= 0.8
        and f.outing_capability >= 0.7
    ):
        return Stage.RECOVERY_MAINTAINED

    # 안정기
    if (
        f.avg_7d_status_score >= 3
        and f.avg_7d_action_score >= 2.0
        and f.avg_7d_task_completion_rate >= 0.7
        and f.avg_7d_available_time >= 30
        and f.recent_3d_need_count == 0
    ):
        return Stage.STABLE

    # 시도기
    if (
        f.avg_7d_status_score > 0.5
        and f.avg_7d_action_score >= 1.0
        and f.avg_7d_task_completion_rate >= 0.5
        and f.outing_capability >= 0.4
    ):
        return Stage.ATTEMPTING

    # 점수가 -3 초과이면 정체기
    if f.avg_7d_status_score > -3:
        return Stage.STAGNANT

    # 점수가 -3 이하일 때 혼란기 전체 조건 확인
    if (
        f.avg_7d_action_score <= -1.0
        and f.avg_7d_task_completion_rate < 0.1
        and f.recent_3d_need_count >= 2
    ):
        return Stage.CHAOS

    # 점수는 -3 이하지만 혼란기 요건 미충족 → 정체기로 분류
    return Stage.STAGNANT


def _is_stagnant_held(f: RecoveryFeatures) -> bool:
    """정체기 유지 조건 — 하나라도 해당하면 상승 차단."""
    # 물리적 제약
    if f.avg_7d_available_time <= 10 and f.recent_3d_no_outing_count >= 2:
        return True
    # 심리적 제약
    if f.recent_3d_need_count == 3:
        return True
    # 행동 부족
    if f.avg_7d_action_score < 1.0:
        return True
    return False


def _apply_transition(f: RecoveryFeatures, raw: Stage) -> Stage:
    """상승 3일 연속 / 하락 2일 연속 전이 규칙을 적용한다."""
    current = f.current_stage

    if raw > current:
        # 고위험군(risk=3) → 시도기 진입은 4일 연속 필요
        required = 4 if (f.onboarding_risk_level == 3 and raw == Stage.ATTEMPTING) else 3
        if f.consecutive_qualifying_days >= required:
            # 당일 need_score == -1.0 이면 승급 하루 보류 (정수로 비교)
            if int(round(f.today_need_score)) == -1:
                return current
            return raw
        return current

    if raw < current:
        if f.consecutive_lower_days >= 2:
            return raw
        return current

    return current
