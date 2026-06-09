from dataclasses import dataclass
from datetime import date
from datetime import datetime
from typing import Optional


@dataclass
class DailyStatusCheck:
    user_disaster_id: int
    check_date: date
    emotion_score: int
    condition_score: int
    action_score: float
    change_score: int
    need_score: float
    available_time: int = 0
    can_go_out: bool = False
    daily_check_id: Optional[int] = None

    @property
    def total_score(self) -> int:
        return int(
            self.emotion_score
            + self.condition_score
            + self.action_score
            + self.change_score
            + self.need_score
        )


@dataclass(frozen=True)
class HomeSummary:
    user_disaster_id: int
    user_name: str | None
    disaster_title: str | None
    disaster_type_name: str | None
    occurred_at: datetime
    recovery_stage_name: str
    recovery_progress: float
    today_total_tasks: int
    today_completed_tasks: int
    daily_status_checked: bool

    @property
    def today_completion_rate(self) -> float:
        if self.today_total_tasks == 0:
            return 0.0
        return round((self.today_completed_tasks / self.today_total_tasks) * 100, 1)


@dataclass(frozen=True)
class TodayTask:
    checklist_item_id: int
    title: str
    priority: int
    is_completed: bool
    is_ai_generated: bool
