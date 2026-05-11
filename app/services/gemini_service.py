import json
import os
import google.generativeai as genai
from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.models import onboarding as onboard_models

# Gemini API Key 설정 (환경변수에서 불러오기)
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# Enum을 한국어로 변환하는 헬퍼 딕셔너리
TIME_MAP = {
    "UNDER_ONE_HOUR": "1시간 이내",
    "ONE_TO_THREE_HOURS": "1~3시간",
    "HALF_DAY": "반나절",
    "ALL_DAY": "하루 종일"
}

def build_disaster_prompt(db: Session, impact: onboard_models.DisasterImpact) -> str:
    # 1. 재난별 상세 정보 조회 (어떤 재난 테이블에 값이 있는지 확인)
    flood = db.query(onboard_models.FloodImpact).filter_by(impact_id=impact.impact_id).first()
    typhoon = db.query(onboard_models.TyphoonImpact).filter_by(impact_id=impact.impact_id).first()
    earthquake = db.query(onboard_models.EarthquakeImpact).filter_by(impact_id=impact.impact_id).first()
    fire = db.query(onboard_models.FireImpact).filter_by(impact_id=impact.impact_id).first()

    disaster_str = ""
    
    # 2. 재난 유형에 따른 동적 문자열 생성
    if flood:
        disaster_str = f"""
- 재난 유형: 홍수 (FLOOD)
- 침수 정도: {flood.flood_level}
- 물 빠짐 상태: {flood.water_drain_status}
- 주거 공간 피해: {flood.damage_house}
- 차량 피해: {flood.damage_vehicle}
- 전기 문제: {flood.electric_problem}
- 수도 문제: {flood.water_problem}"""
    elif typhoon:
        disaster_str = f"""
- 재난 유형: 태풍 (TYPHOON)
- 지붕 파손 여부: {typhoon.roof_damage}
- 창문 파손 여부: {typhoon.window_damage}
- 구조물 피해: {typhoon.structure_damage}
- 차량 피해: {typhoon.vehicle_damage}
- 전기 문제: {typhoon.electric_problem}
- 수도 문제: {typhoon.water_problem}"""
    elif earthquake:
        disaster_str = f"""
- 재난 유형: 지진 (EARTHQUAKE)
- 여진 체감 여부: {earthquake.aftershock_feeling}
- 건물 균열 여부: {earthquake.building_crack}
- 주거 공간 피해: {earthquake.house_damage}
- 차량 피해: {earthquake.vehicle_damage}
- 전기 문제: {earthquake.electric_problem}
- 수도 문제: {earthquake.water_problem}"""
    elif fire:
        disaster_str = f"""
- 재난 유형: 화재 (FIRE)
- 화재 피해 범위: {fire.fire_damage_scope}
- 연기 흡입 정도: {fire.smoke_inhalation}
- 주거 공간 피해: {fire.house_damage}
- 그을음 피해: {fire.soot_damage}
- 잔해 존재 여부: {fire.debris_exist}
- 차량 피해: {fire.vehicle_damage}
- 전기 문제: {fire.electric_problem}
- 수도 문제: {fire.water_problem}"""

    # 3. 사용자 상태 문자열 생성 (TODO 반영)
    can_go_out_str = "가능(TRUE)" if impact.can_go_out else "불가능(FALSE)"
    avail_time_str = TIME_MAP.get(impact.available_time, "알 수 없음")

    prompt = f"""사용자는 재난 이후 회복 과정에 있습니다. 다음 정보를 바탕으로 오늘 수행할 맞춤형 체크리스트를 생성해주세요.

[재난 상황]{disaster_str}
- 안전 상태: {impact.safty_status}
- 거주 상태: {impact.residence_status}

[사용자 상태]
- 회복 단계: TRYING (TODO: 추후 DB 연동 필요)
- 주간 달성률: 0.65 (TODO: 추후 DB 연동 필요)
- 외출 가능 여부: {can_go_out_str}
- 외출 가능 시간: {avail_time_str}

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
    return prompt

def generate_checklist_from_gemini(prompt: str) -> list[str]:
    try:
        # JSON 형태로 강제 반환하도록 설정
        model = genai.GenerativeModel(
            'gemini-1.5-flash', # 혹은 gemini-1.5-pro
            generation_config={"response_mime_type": "application/json"}
        )
        response = model.generate_content(prompt)
        
        # JSON 파싱
        json_data = json.loads(response.text)
        
        # 타이틀만 추출
        titles = [item["title"] for item in json_data]
        
        # 혹시 3개가 아닐 경우 방어 로직
        if len(titles) > 3:
            titles = titles[:3]
        elif len(titles) < 3:
            titles += ["안전 상태 다시 한번 확인하기"] * (3 - len(titles)) # 부족할 경우 기본값
            
        return titles
    except Exception as e:
        print(f"Gemini API Error: {str(e)}")
        # API 오류 발생 시 폴백(Fallback) 기본 체크리스트 제공
        return ["가족 지인에게 안전 연락하기", "파손된 물건 사진 찍어두기", "식수 및 비상식량 확인하기"]