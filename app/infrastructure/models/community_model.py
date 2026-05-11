"""Community 도메인 ORM — DDL에 정의된 테이블만 (댓글/스크랩 등 확장 테이블 없음)."""

from datetime import datetime
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import BigInteger, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.infrastructure.models.base import TimestampMixin

if TYPE_CHECKING:
    from app.infrastructure.models.user_model import UserModel


class CommunityProfileModel(TimestampMixin, Base):
    __tablename__ = "community_profiles"

    community_profile_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("Users.user_id", ondelete="CASCADE"), nullable=False, unique=True
    )
    intro_message: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    contribution_badge: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    contribution_score: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    user: Mapped["UserModel"] = relationship(back_populates="community_profile")
    posts: Mapped[List["CommunityPostModel"]] = relationship(back_populates="author_profile")


class CommunityCategoryModel(TimestampMixin, Base):
    # [수정] "community categories" → "community_categories" (테이블명 공백 제거)
    __tablename__ = "community_categories"

    community_category_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    category_code: Mapped[str] = mapped_column(String(30), nullable=False, unique=True)
    category_name: Mapped[str] = mapped_column(String(50), nullable=False)
    description: Mapped[str] = mapped_column(String(255), nullable=False)

    posts: Mapped[List["CommunityPostModel"]] = relationship(back_populates="category")


class CommunityPostModel(TimestampMixin, Base):
    __tablename__ = "community_posts"

    community_posts_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("Users.user_id"), nullable=False, index=True)
    user_disaster_id: Mapped[int] = mapped_column(
        "user__disaster_id",
        Integer,
        ForeignKey("user_disasters.user__disaster_id"),
        nullable=False,
    )
    residence_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("user_residences.residence_id"), nullable=False
    )
    # [수정] FK 참조 테이블명 "community categories" → "community_categories"
    community_category_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("community_categories.community_category_id"), nullable=False
    )
    post_type: Mapped[str] = mapped_column(String(30), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    # [수정] Optional[int] nullable=True → int nullable=False DEFAULT 0 (카운터 컬럼)
    view_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    comment_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    empathy_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    scrap_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    author_profile: Mapped["CommunityProfileModel"] = relationship(
        back_populates="posts",
        foreign_keys=[user_id],
        primaryjoin="CommunityPostModel.user_id == CommunityProfileModel.user_id",
        viewonly=True,
    )
    category: Mapped["CommunityCategoryModel"] = relationship(back_populates="posts")
    links: Mapped[List["CommunityPostLinkModel"]] = relationship(
        back_populates="post", cascade="all, delete-orphan"
    )
    attachments: Mapped[List["CommunityPostAttachmentModel"]] = relationship(
        back_populates="post", cascade="all, delete-orphan"
    )


class CommunityPostLinkModel(Base):
    __tablename__ = "community_post_links"

    community_post_link_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    community_posts_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("community_posts.community_posts_id", ondelete="CASCADE"), nullable=False
    )
    link_url: Mapped[str] = mapped_column(String(1000), nullable=False)
    link_title: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    display_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())

    post: Mapped["CommunityPostModel"] = relationship(back_populates="links")


class CommunityPostAttachmentModel(Base):
    __tablename__ = "community_posts_attachments"

    community_post_attachment_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    community_posts_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("community_posts.community_posts_id", ondelete="CASCADE"), nullable=False
    )
    attachment_type: Mapped[str] = mapped_column(String(20), nullable=False)
    file_url: Mapped[str] = mapped_column(String(500), nullable=False)
    original_file_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    mime_type: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    file_size: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    display_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())

    post: Mapped["CommunityPostModel"] = relationship(back_populates="attachments")