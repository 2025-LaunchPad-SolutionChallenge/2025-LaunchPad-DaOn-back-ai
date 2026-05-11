from sqlalchemy.orm import Session
from app.models.onboarding import DisasterImpact


def create_impact(db: Session, data: dict):
    impact = DisasterImpact(**data)
    db.add(impact)
    db.commit()
    db.refresh(impact)
    return impact


def get_disaster(db: Session, disaster_id: int):
    from app.models.disaster import Disaster
    return db.query(Disaster).filter(Disaster.id == disaster_id).first()