from dataclasses import dataclass
from enum import IntEnum


class Stage(IntEnum):
    CHAOS = 1
    STAGNANT = 2
    ATTEMPTING = 3
    STABLE = 4
    RECOVERY_MAINTAINED = 5

    def to_db_str(self) -> str:
        """DB predicted_stage 컬럼에 저장하는 문자열."""
        _map = {
            Stage.CHAOS: "CHAOS",
            Stage.STAGNANT: "STAGNANT",
            Stage.ATTEMPTING: "ATTEMPTING",
            Stage.STABLE: "STABLE",
            Stage.RECOVERY_MAINTAINED: "MAINTAINED",
        }
        return _map[self]

    @staticmethod
    def from_db_str(value: str) -> "Stage":
        _map = {
            "CHAOS": Stage.CHAOS,
            "STAGNANT": Stage.STAGNANT,
            "ATTEMPTING": Stage.ATTEMPTING,
            "STABLE": Stage.STABLE,
            "MAINTAINED": Stage.RECOVERY_MAINTAINED,
        }
        return _map[value]


@dataclass
class RecoveryFeatures:
    # ── 7일 평균 지표 (RecoveryFeatureModel에서 계산) ─────────────────
    avg_7d_status_score: float          # 7일 평균 상태 점수
    avg_7d_action_score: float          # 7일 평균 행동 점수
    avg_7d_task_completion_rate: float  # 7일 체크리스트 달성률 (0.0~1.0)
    outing_capability: float            # 7일 중 외출 가능 비율 (0.0~1.0)
    avg_7d_available_time: float        # 7일 평균 가용 시간 (정수 단위)

    # ── 최근 3일 집계 (DailyStatusCheckModel에서 계산) ────────────────
    recent_3d_need_count: int           # need_score == -1.0 인 날 수
    recent_3d_no_outing_count: int      # can_go_out == False 인 날 수

    # ── 온보딩 컨텍스트 ────────────────────────────────────────────────
    onboarding_risk_level: int          # 1~3
    days_since_disaster: int            # 재난 등록일로부터 경과 일 수
    current_stage: Stage                # 현재 DB에 저장된 단계

    # ── 전이 이력 (배치 잡에서 사전 계산) ─────────────────────────────
    consecutive_qualifying_days: int    # 상위 단계 조건을 연속 만족한 날 수
    consecutive_lower_days: int         # 하위 단계 조건을 연속 만족한 날 수
    recent_2d_crisis: bool              # 2일 연속 (can_go_out=False AND 완료=0)

    # ── 당일 데이터 ────────────────────────────────────────────────────
    today_need_score: float             # 승급 보류 판정용
    today_completions: int              # 오늘 완료한 체크리스트 수
    today_can_go_out: bool

    # ── 회복 유지기 안정성 ─────────────────────────────────────────────
    recent_14d_below_stable: bool       # 최근 14일 중 Stable 이하 조건 발생 여부
    missing_days_last_14d: int          # 최근 14일 중 데이터 미입력 일 수
