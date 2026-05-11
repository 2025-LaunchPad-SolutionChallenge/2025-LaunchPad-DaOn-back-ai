from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, BigInteger
from sqlalchemy.sql import func
from app.db.base import Base

# 테이블 구조를 SQLAlchemy 객체로 매핑

class DisasterImpact(Base):
    __tablename__ = "disaster_impacts"
    
    impact_id = Column(Integer, primary_key=True, index=True)
    user__disaster_id = Column(Integer, nullable=False)
    safty_status = Column(String(50), nullable=True) # DB 오타 유지
    residence_status = Column(String(50), nullable=False)
    injury_level = Column(String(50), nullable=False)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)

class DisasterTypeModel(Base):
    __tablename__ = "disaster_types"
    
    disaster_type_id = Column(Integer, primary_key=True, index=True)
    disaster_code = Column(String, nullable=False) 
    disaser_name = Column(String, nullable=True)   
    description = Column(String, nullable=True)

class FloodImpact(Base):
    __tablename__ = "flood_impacts"
    
    flood_impact_id = Column(BigInteger, primary_key=True, index=True)
    flood_level = Column(String(50), nullable=False)
    water_drain_status = Column(String(50), nullable=False)
    damage_house = Column(Boolean, default=False, nullable=False)
    damage_vehicle = Column(Boolean, default=False, nullable=False)
    electric_problem = Column(Boolean, default=False, nullable=False)
    water_problem = Column(Boolean, default=False, nullable=False)
    impact_id = Column(Integer, ForeignKey("disaster_impacts.impact_id"), nullable=False)

class TyphoonImpact(Base):
    __tablename__ = "typhoon_impacts"
    
    typhoon_impact_id = Column(BigInteger, primary_key=True, index=True)
    roof_damage = Column(Boolean, default=False, nullable=False)
    window_damage = Column(Boolean, default=False, nullable=False)
    structure_damage = Column(Boolean, default=False, nullable=False)
    vehicle_damage = Column(Boolean, default=False, nullable=False)
    electric_problem = Column(Boolean, default=False, nullable=False)
    water_problem = Column(Boolean, default=False, nullable=False)
    impact_id = Column(Integer, ForeignKey("disaster_impacts.impact_id"), nullable=False)

class EarthquakeImpact(Base):
    __tablename__ = "earthquake_impacts"
    
    earth_impact_id = Column(BigInteger, primary_key=True, index=True)
    aftershock_feeling = Column(String(50), nullable=False)
    building_crack = Column(Boolean, default=False, nullable=False)
    house_damage = Column(Boolean, default=False, nullable=False)
    vehicle_damage = Column(Boolean, default=False, nullable=False)
    electric_problem = Column(Boolean, default=False, nullable=False)
    water_problem = Column(Boolean, default=False, nullable=False)
    impact_id = Column(Integer, ForeignKey("disaster_impacts.impact_id"), nullable=False)

class FireImpact(Base):
    __tablename__ = "fire_impacts"
    
    fire_impact_id = Column(BigInteger, primary_key=True, index=True)
    fire_damage_scope = Column(String(50), nullable=False)
    smoke_inhalation = Column(String(50), nullable=False)
    house_damage = Column(Boolean, default=False, nullable=False)
    soot_damage = Column(Boolean, default=False, nullable=False)
    debris_exist = Column(Boolean, default=False, nullable=False)
    vehicle_damage = Column(Boolean, default=False, nullable=False)
    electric_problem = Column(Boolean, default=False, nullable=False)
    water_problem = Column(Boolean, default=False, nullable=False)
    impact_id = Column(Integer, ForeignKey("disaster_impacts.impact_id"), nullable=False)