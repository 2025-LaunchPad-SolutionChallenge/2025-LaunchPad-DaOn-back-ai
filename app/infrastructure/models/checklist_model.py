"""Checklist 도메인 ORM — DDL 컬럼·테이블명과 동일."""

from datetime import date, datetime
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import BigInteger, Boolean, Date, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.infrastructure.models.base import TimestampMixin

if TYPE_CHECKING:
    from app.infrastructure.models.disaster_model import UserDisasterModel


class ChecklistItemModel(TimestampMixin, Base):
    __tablename__ = "checklist_items"

    checklist_item_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_disaster_id: Mapped[int] = mapped_column(
        "user__disaster_id",
        Integer,
        ForeignKey("user_disasters.user__disaster_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    checklist_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    memo: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    item_source_type: Mapped[str] = mapped_column(String(30), nullable=False)
    priority: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    is_completed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    user_disaster: Mapped["UserDisasterModel"] = relationship(back_populates="checklist_items")
    archive_items: Mapped[List["ArchiveItemModel"]] = relationship(
        back_populates="checklist_item", cascade="all, delete-orphan"
    )


class ArchiveItemModel(TimestampMixin, Base):
    __tablename__ = "archive_items"

    archive_item_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_setting_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("user_settings.user_setting_id"), nullable=False
    )
    checklist_item_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("checklist_items.checklist_item_id", ondelete="CASCADE"), nullable=False, index=True
    )
    archive_date: Mapped[date] = mapped_column(Date, nullable=False)
    archive_type: Mapped[str] = mapped_column(String(20), nullable=False)
    title: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    checklist_item: Mapped["ChecklistItemModel"] = relationship(back_populates="archive_items")
    files: Mapped[List["ArchiveFileModel"]] = relationship(
        back_populates="archive_item", cascade="all, delete-orphan"
    )


class ArchiveFileModel(Base):
    __tablename__ = "archive_files"

    archive_file_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    archive_item_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("archive_items.archive_item_id", ondelete="CASCADE"), nullable=False, index=True
    )
    original_file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    stored_file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    file_url: Mapped[str] = mapped_column(String(500), nullable=False)
    mime_type: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    file_size: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    thumbnail_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())

    archive_item: Mapped["ArchiveItemModel"] = relationship(back_populates="files")
