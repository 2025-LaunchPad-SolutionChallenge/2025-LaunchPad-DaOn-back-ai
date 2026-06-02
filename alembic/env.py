"""
Alembic 마이그레이션 실행 환경 설정.

변경 사항 (기본 템플릿 대비):
  - target_metadata = None  →  Base.metadata  (autogenerate 활성화)
  - DATABASE_URL 을 app.config.settings 에서 주입  (alembic.ini 직접 수정 불필요)
  - async SQLAlchemy 엔진에 맞게 async 방식으로 마이그레이션 실행
  - compare_type=True  →  ENUM·VARCHAR 길이 변경도 감지
"""

import asyncio
from logging.config import fileConfig

from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from alembic import context

# app.config.settings 에서 DATABASE_URL 을 읽어옴
from app.config import settings

# Base.metadata 를 가져와 autogenerate 타깃으로 설정
from app.database import Base

# 모든 ORM 모델을 import해야 Base.metadata 에 테이블이 등록됨
# (import 자체가 사이드 이펙트이므로 noqa 처리)
import app.infrastructure.models  # noqa: F401

# ── Alembic Config ────────────────────────────────────────────────────────────
config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# alembic.ini 의 sqlalchemy.url 대신 settings 값을 런타임에 주입
# → alembic.ini 에 DB 비밀번호를 평문으로 남기지 않아도 됨
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)

# autogenerate 가 비교할 메타데이터 (None 이면 아무 테이블도 감지 안 됨)
target_metadata = Base.metadata


# ── Offline 모드 ──────────────────────────────────────────────────────────────
def run_migrations_offline() -> None:
    """
    실제 DB 연결 없이 URL 만으로 마이그레이션 SQL 을 생성한다.
    CI 환경이나 dry-run 용도로 사용.
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,  # ENUM·컬럼 타입 변경 감지
    )
    with context.begin_transaction():
        context.run_migrations()


# ── Online 모드 ───────────────────────────────────────────────────────────────
def do_run_migrations(connection: Connection) -> None:
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,  # ENUM·컬럼 타입 변경 감지
    )
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """비동기 엔진을 생성하고 sync 래퍼를 통해 마이그레이션을 실행한다."""
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,  # 마이그레이션은 커넥션 풀 불필요
    )
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()


def run_migrations_online() -> None:
    asyncio.run(run_async_migrations())


# ── 진입점 ────────────────────────────────────────────────────────────────────
if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()