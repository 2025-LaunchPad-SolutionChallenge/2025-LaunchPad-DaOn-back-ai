"""통합 테스트: .env보다 먼저 기본 환경을 두고, Alembic을 세션 시작 시 1회 적용."""

from __future__ import annotations

import asyncio
import os
import subprocess
import sys
import time
from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parents[1]


def pytest_configure() -> None:
    os.environ.setdefault("MYSQL_HOST", "127.0.0.1")
    os.environ.setdefault("MYSQL_PORT", "3306")
    os.environ.setdefault("MYSQL_USER", "appuser")
    os.environ.setdefault("MYSQL_PASSWORD", "appsecret")
    os.environ.setdefault("MYSQL_DB", "launchpad")
    os.environ.setdefault("JWT_SECRET_KEY", "integration-test-secret-key-min-32-chars!")
    os.environ.setdefault("JWT_ALGORITHM", "HS256")
    os.environ.setdefault("ACCESS_TOKEN_EXPIRE_MINUTES", "60")
    os.environ.setdefault("REFRESH_TOKEN_EXPIRE_DAYS", "30")
    os.environ.setdefault("FIREBASE_CREDENTIALS_PATH", str(_ROOT / "tests" / "fixtures" / "dummy_firebase_admin.json"))
    os.environ.setdefault("APP_NAME", "Integration Test API")


def _wait_mysql() -> None:
    import pymysql

    host = os.environ["MYSQL_HOST"]
    port = int(os.environ.get("MYSQL_PORT", "3306"))
    user = os.environ["MYSQL_USER"]
    password = os.environ["MYSQL_PASSWORD"]
    database = os.environ["MYSQL_DB"]
    last: Exception | None = None
    for _ in range(90):
        try:
            conn = pymysql.connect(
                host=host,
                port=port,
                user=user,
                password=password,
                database=database,
                connect_timeout=2,
            )
            conn.close()
            return
        except Exception as e:  # noqa: BLE001
            last = e
            time.sleep(1)
    raise RuntimeError(f"MySQL not reachable at {host}:{port}/{database}: {last}") from last


def pytest_sessionstart(session) -> None:
    _wait_mysql()
    env = os.environ.copy()
    env.setdefault("PYTHONPATH", str(_ROOT))
    subprocess.run(
        [sys.executable, "-m", "alembic", "upgrade", "head"],
        cwd=_ROOT,
        check=True,
        env=env,
    )


@pytest.fixture(autouse=True)
def _dispose_async_engine_pool_after_test() -> None:
    """TestClient마다 이벤트 루프가 바뀌므로, 풀에 남은 연결을 비워 다음 테스트에서 루프 충돌을 막음."""
    yield
    from app.database import engine

    asyncio.run(engine.dispose())
