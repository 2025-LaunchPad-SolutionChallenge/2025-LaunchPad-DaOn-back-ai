from sqlalchemy.orm import Session
from app.models import onboarding as models
from app.schemas import onboarding as schemas

# damages 배열의 순서 인덱스를 기반으로 DB컬럼에 각각 매핑
def create_disaster_impact(db: Session, req: schemas.OnboardingRequest) -> models.DisasterImpact:
    db_impact = models.DisasterImpact(
        user__disaster_id=req.disaster_id,
        safty_status=req.safety_status.value if req.safety_status else None,
        residence_status=req.residence_status.value,
        injury_level=req.injury_level.value
    )
    db.add(db_impact)
    db.commit()
    db.refresh(db_impact)
    return db_impact

def create_flood_impact(db: Session, data: dict):
    db_flood = models.FloodImpact(**data)
    db.add(db_flood)
    db.commit()

def create_typhoon_impact(db: Session, data: dict):
    db_typhoon = models.TyphoonImpact(**data)
    db.add(db_typhoon)
    db.commit()

def create_earthquake_impact(db: Session, data: dict):
    db_earthquake = models.EarthquakeImpact(**data)
    db.add(db_earthquake)
    db.commit()

def create_fire_impact(db: Session, data: dict):
    db_fire = models.FireImpact(**data)
    db.add(db_fire)
    db.commit()

# 상황 데이터 입력 후 업데이트 함수
def update_disaster_context(db: Session, req: schemas.ContextRequest) -> models.DisasterImpact:
    db_impact = db.query(models.DisasterImpact).filter(
        models.DisasterImpact.user__disaster_id == req.user_disaster_id
    ).first()
    
    if not db_impact:
        return None 
        
    db_impact.can_go_out = req.user_condition.can_go_out
    db_impact.available_time = req.user_condition.available_time.value 
    
    db.commit()
    db.refresh(db_impact)
    return db_impact