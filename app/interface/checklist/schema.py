from datetime import date
from typing import List

from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel


class CamelModel(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)


class ChecklistGenerateRequest(CamelModel):
    user_disaster_id: int
    target_date: date


class GeneratedItemInfo(CamelModel):
    checklist_item_id: int
    title: str
    item_source_type: str


class ChecklistGenerateResponse(CamelModel):
    items: List[GeneratedItemInfo]
