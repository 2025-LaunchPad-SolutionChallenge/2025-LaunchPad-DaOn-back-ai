from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, JSON
from app.db.base import Base


class DisasterImpact(Base):
    __tablename__ = "disaster_impact"

    id = Column(Integer, primary_key=True, index=True)
    disaster_id = Column(Integer, ForeignKey("disaster.id"))

    safety_status = Column(String)
    residence_status = Column(String)
    injury_level = Column(String)

    detail_type = Column(String)  # flood, typhoon 등
    detail_data = Column(JSON)     # floodDetail JSON 저장