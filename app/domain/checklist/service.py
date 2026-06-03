import json
import os
from datetime import date
from typing import List

import google.generativeai as genai

from app.common.exceptions import NotFoundException
from app.domain.checklist.entity import ChecklistItem
from app.domain.checklist.repository import ChecklistRepository
from app.domain.disaster.entity import DisasterImpactFull

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

_TIME_MAP = {
    "UNDER_ONE_HOUR": "1시간 이내",
    "ONE_TO_THREE_HOURS": "1~3시간",
    "HALF_DAY": "반나절",
    "ALL_DAY": "하루 종일",
}


def _build_prompt(
    full: DisasterImpactFull,
    recovery_stage: str,
    weekly_progress: float,
) -> str:
    impact = full.impact
    disaster_str = ""

    if full.flood_detail:
        d = full.flood_detail
        disaster_str = f"""
- 재난 유형: 홍수 (FLOOD)
- 침수 정도: {d.flood_level}
- 물 빠짐 상태: {d.water_drain_status}
- 주거 공간 피해: {d.damage_house}
- 차량 피해: {d.damage_vehicle}
- 전기 문제: {d.electric_problem}
- 수도 문제: {d.water_problem}"""
    elif full.typhoon_detail:
        d = full.typhoon_detail
        disaster_str = f"""
- 재난 유형: 태풍 (TYPHOON)
- 지붕 파손 여부: {d.roof_damage}
- 창문 파손 여부: {d.window_damage}
- 구조물 피해: {d.structure_damage}
- 차량 피해: {d.vehicle_damage}
- 전기 문제: {d.electric_problem}
- 수도 문제: {d.water_problem}"""
    elif full.earthquake_detail:
        d = full.earthquake_detail
        disaster_str = f"""
- 재난 유형: 지진 (EARTHQUAKE)
- 여진 체감 여부: {d.aftershock_feeling}
- 건물 균열 여부: {d.building_crack}
- 주거 공간 피해: {d.house_damage}
- 차량 피해: {d.vehicle_damage}
- 전기 문제: {d.electric_problem}
- 수도 문제: {d.water_problem}"""
    elif full.fire_detail:
        d = full.fire_detail
        disaster_str = f"""
- 재난 유형: 화재 (FIRE)
- 화재 피해 범위: {d.fire_damage_scope}
- 연기 흡입 정도: {d.smoke_inhalation}
- 주거 공간 피해: {d.house_damage}
- 그을음 피해: {d.soot_damage}
- 잔해 존재 여부: {d.debris_exist}
- 차량 피해: {d.vehicle_damage}
- 전기 문제: {d.electric_problem}
- 수도 문제: {d.water_problem}"""

    can_go_out_str = "가능(TRUE)" if impact.can_go_out else "불가능(FALSE)"
    avail_time_str = _TIME_MAP.get(impact.available_time or "", "알 수 없음")

    return f"""사용자는 재난 이후 회복 과정에 있습니다. 다음 정보를 바탕으로 오늘 수행할 맞춤형 체크리스트를 생성해주세요.

[재난 상황]{disaster_str}
- 안전 상태: {impact.safety_status}
- 거주 상태: {impact.residence_status}

[사용자 상태]
- 회복 단계: {recovery_stage}
- 외출 가능 여부: {can_go_out_str}
- 외출 가능 시간: {avail_time_str}
- 주간 달성률: {weekly_progress:.2f}

조건:
1. 반드시 딱 3개의 할 일(title)만 생성할 것
2. 현실적으로 수행 가능해야 함
3. 회복 단계에 맞는 난이도
4. 구체적인 행동 단위 (예: "젖은 옷가지 세탁하기", "전기 안전 점검 신청하기")

반드시 아래 JSON 형식으로만 반환하세요 (마크다운 백틱 등 다른 텍스트는 일절 포함하지 마세요):
[
  {{"title": "..."}},
  {{"title": "..."}},
  {{"title": "..."}}
]"""


def _call_gemini(prompt: str) -> List[str]:
    try:
        model = genai.GenerativeModel(
            "gemini-1.5-flash",
            generation_config={"response_mime_type": "application/json"},
        )
        response = model.generate_content(prompt)
        titles = [item["title"] for item in json.loads(response.text)]
        if len(titles) > 3:
            titles = titles[:3]
        elif len(titles) < 3:
            titles += ["안전 상태 다시 한번 확인하기"] * (3 - len(titles))
        return titles
    except Exception as e:
        print(f"Gemini API Error: {e}")
        return ["가족 지인에게 안전 연락하기", "파손된 물건 사진 찍어두기", "식수 및 비상식량 확인하기"]


async def generate_ai_checklist(
    repo: ChecklistRepository,
    impact_full: DisasterImpactFull,
    user_disaster_id: int,
    target_date: date,
    recovery_stage: str = "CHAOS",
    weekly_progress: float = 0.0,
) -> List[ChecklistItem]:
    if not impact_full:
        raise NotFoundException("해당 사용자의 재난 온보딩 정보가 존재하지 않습니다.")

    prompt = _build_prompt(impact_full, recovery_stage, weekly_progress)
    titles = _call_gemini(prompt)
    items = [
        ChecklistItem(
            user_disaster_id=user_disaster_id,
            checklist_date=target_date,
            title=title,
            item_source_type="AI_GENERATED",
            priority=idx + 1,
        )
        for idx, title in enumerate(titles)
    ]
    return await repo.save_items(items)
