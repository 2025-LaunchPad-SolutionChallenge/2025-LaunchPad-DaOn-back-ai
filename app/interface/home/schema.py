from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel


class CamelModel(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)


class DailyStatusRequest(CamelModel):
    emotion_score: int
    energy_score: int
    activity_score: int
    recovery_score: int
    need_score: int


class DailyStatusResponse(CamelModel):
    daily_check_id: int
    total_score: int
    message: str
