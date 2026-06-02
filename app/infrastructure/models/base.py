"""
공통 Mixin 클래스 모음.

여러 모델이 공통으로 갖는 컬럼(created_at, updated_at)을
Mixin으로 분리해서 중복 없이 상속받아 사용.

사용 예시:
    class UserModel(TimestampMixin, Base):
        __tablename__ = "users"
        ...
"""

from datetime import datetime
from sqlalchemy import DateTime, func
from sqlalchemy.orm import Mapped, mapped_column


class TimestampMixin:
    """
    created_at, updated_at 자동 관리 Mixin.

    created_at: 레코드 최초 생성 시각 (INSERT 시 자동 설정, 이후 변경 불가)
    updated_at: 레코드 마지막 수정 시각 (INSERT/UPDATE 시 자동 갱신)

    server_default / onupdate: Python이 아닌 DB 레벨에서 처리
    → 직접 값을 넣지 않아도 DB가 자동으로 채워줌
    """
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=func.now(),   # INSERT 시 DB가 현재 시각으로 자동 설정
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),         # UPDATE 시 DB가 현재 시각으로 자동 갱신
    )
