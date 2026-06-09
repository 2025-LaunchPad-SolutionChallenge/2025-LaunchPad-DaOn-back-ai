from dataclasses import dataclass
from datetime import date
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
