from sqlalchemy import Column, Integer, String, Boolean, DateTime, Date, BigInt
from sqlalchemy.sql import func
from app.database import Base

class ChecklistItem(Base):
    __tablename__ = "checklist_items"
    
    checklist_item_id = Column(BigInt, primary_key=True, index=True)
    user__disaster_id = Column(Integer, nullable=False)
    checklist_date = Column(Date, nullable=False)
    title = Column(String(255), nullable=False)
    memo = Column(String(255), nullable=True)
    item_source_type = Column(String(30), nullable=False) # AI_GENERATED, USER_CREATED, AI_MODIFIED
    priority = Column(Integer, default=1, nullable=False)
    is_completed = Column(Boolean, default=False, nullable=False)
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)