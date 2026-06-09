from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel


class CamelModel(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)


class DailyStatusRequest(CamelModel):
    emotion_score: int = Field(..., description="감정 점수")
    energy_score: int = Field(..., description="에너지 점수")
    activity_score: int = Field(..., description="활동 점수")
    recovery_score: int = Field(..., description="회복 체감 점수")
    need_score: int = Field(..., description="도움 필요도 점수")


class DailyStatusResponse(CamelModel):
    daily_check_id: int = Field(..., description="저장된 일일 상태 체크 ID")
    total_score: int = Field(..., description="입력 점수 합산값")
    message: str = Field(..., description="처리 결과 메시지")


class DailyStatusLookupResponse(CamelModel):
    checked: bool = Field(..., description="오늘 상태 체크 완료 여부")
    daily_check_id: int | None = Field(default=None, description="오늘 상태 체크 ID")
    emotion_score: int | None = Field(default=None, description="감정 점수")
    energy_score: int | None = Field(default=None, description="에너지 점수")
    activity_score: float | None = Field(default=None, description="활동 점수")
    recovery_score: int | None = Field(default=None, description="회복 체감 점수")
    need_score: float | None = Field(default=None, description="도움 필요도 점수")
    total_score: int | None = Field(default=None, description="총점")
    message: str = Field(..., description="처리 결과 메시지")


class HomeSummaryResponse(CamelModel):
    user_disaster_id: int = Field(..., description="활성 재난 ID")
    user_name: str | None = Field(default=None, description="사용자 이름")
    disaster_title: str | None = Field(default=None, description="재난 제목")
    disaster_type_name: str | None = Field(default=None, description="재난 유형명")
    occurred_at: str = Field(..., description="재난 발생 시각 (ISO8601 문자열)")
    recovery_stage_name: str = Field(..., description="현재 회복 단계명")
    recovery_progress: float = Field(..., description="회복 진행률(0~100)")
    daily_status_checked: bool = Field(..., description="오늘 상태 체크 여부")
    today_total_tasks: int = Field(..., description="오늘 전체 체크리스트 개수")
    today_completed_tasks: int = Field(..., description="오늘 완료한 체크리스트 개수")
    today_completion_rate: float = Field(..., description="오늘 체크리스트 달성률(%)")


class TodayTaskItemResponse(CamelModel):
    checklist_item_id: int = Field(..., description="체크리스트 항목 ID")
    title: str = Field(..., description="할 일 제목")
    priority: int = Field(..., description="우선순위")
    is_completed: bool = Field(..., description="완료 여부")
    is_ai_generated: bool = Field(..., description="AI 생성 항목 여부")


class TodayTasksResponse(CamelModel):
    total_count: int = Field(
        ...,
        description=(
            "현재 응답 items 길이입니다. "
            "/home/today-tasks는 최대 3, /home/today-tasks/full은 전체 길이입니다."
        ),
    )
    items: list[TodayTaskItemResponse] = Field(..., description="오늘 할 일 목록")
