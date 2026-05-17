"""Firebase는 모킹하고, 실제 MySQL + Alembic 스키마로 인증 플로우를 검증."""

from __future__ import annotations

import hashlib
import secrets
from contextlib import contextmanager
from unittest.mock import AsyncMock, patch

from starlette.testclient import TestClient

from firebase_admin.exceptions import UnauthenticatedError


def _uid_from_token(token: str) -> str:
    """토큰 문자열당 안정적인 가짜 Firebase uid."""
    digest = hashlib.sha256(token.encode()).hexdigest()[:28]
    return f"fb-{digest}"


async def _fake_verify_firebase_id_token(token: str) -> dict:
    if token == "invalid-firebase-token":
        raise UnauthenticatedError("mock invalid id token")
    # 회원탈퇴: 동일 테스트 DB에서 재실행해도 uid가 겹치지 않도록 suffix 사용
    if "|" in token and token.startswith("firebase-ok-w-"):
        parts = token.split("|")
        if len(parts) >= 2 and parts[1]:
            suffix = parts[1]
            return {
                "uid": f"integration-w-{suffix}",
                "email": None,
                "email_verified": True,
            }
    if token.startswith("firebase-ok-"):
        return {
            "uid": _uid_from_token(token),
            "email": "mock@example.com",
            "email_verified": True,
        }
    raise UnauthenticatedError("unknown mock token")


@contextmanager
def _test_client():
    with patch("app.main.init_firebase", lambda: None):
        with patch(
            "app.domain.auth.service.verify_firebase_id_token",
            side_effect=_fake_verify_firebase_id_token,
        ):
            from app.main import app

            with TestClient(app) as client:
                yield client


def test_register_login_refresh_me_logout_revoked_chain() -> None:
    token = "firebase-ok-" + secrets.token_hex(6)
    with _test_client() as client:
        reg = client.post(
            "/api/v1/auth/register",
            json={
                "firebaseToken": token,
                "name": "통합테스트",
                "birthDate": "1995-03-15",
            },
        )
        assert reg.status_code == 200, reg.text
        body = reg.json()
        assert body["isNewUser"] is True
        assert body["user"]["id"] >= 1
        refresh = body["refreshToken"]
        access = body["accessToken"]

        log = client.post(
            "/api/v1/auth/login",
            json={"firebaseToken": token},
        )
        assert log.status_code == 200, log.text
        assert log.json()["isNewUser"] is False

        old_refresh = refresh
        ref = client.post(
            "/api/v1/auth/refresh",
            json={"refreshToken": old_refresh},
        )
        assert ref.status_code == 200, ref.text
        new_access = ref.json()["accessToken"]
        new_refresh = ref.json()["refreshToken"]
        assert new_refresh != old_refresh

        me = client.get(
            "/api/v1/users/me",
            headers={"Authorization": f"Bearer {new_access}"},
        )
        assert me.status_code == 200, me.text
        payload = me.json()
        assert payload.get("sub")
        assert payload.get("firebase_uid") == _uid_from_token(token)

        out = client.post(
            "/api/v1/auth/logout",
            headers={"Authorization": f"Bearer {new_access}"},
            json={"refreshToken": new_refresh},
        )
        assert out.status_code == 200, out.text
        assert out.json()["message"] == "로그아웃되었습니다."

        bad_refresh = client.post(
            "/api/v1/auth/refresh",
            json={"refreshToken": new_refresh},
        )
        assert bad_refresh.status_code == 401
        assert bad_refresh.json().get("code") == "REVOKED_REFRESH_TOKEN"


def test_login_invalid_firebase_401() -> None:
    with _test_client() as client:
        r = client.post(
            "/api/v1/auth/login",
            json={"firebaseToken": "invalid-firebase-token"},
        )
        assert r.status_code == 401
        assert r.json().get("code") == "INVALID_FIREBASE_TOKEN"


def test_login_unknown_user_404() -> None:
    """검증은 통과하지만 DB에 없는 uid → 404."""
    orphan = "firebase-ok-" + secrets.token_hex(8)
    with _test_client() as client:
        r = client.post(
            "/api/v1/auth/login",
            json={"firebaseToken": orphan},
        )
        assert r.status_code == 404
        assert r.json().get("code") == "USER_NOT_FOUND"


def test_withdraw_deletes_user_and_blocks_login() -> None:
    mock_delete = AsyncMock(return_value=None)
    suffix = secrets.token_hex(4)
    reg_tok = f"firebase-ok-w-reg|{suffix}"
    reauth_tok = f"firebase-ok-w-reauth|{suffix}"
    with patch("app.main.init_firebase", lambda: None):
        with patch(
            "app.domain.auth.service.verify_firebase_id_token",
            side_effect=_fake_verify_firebase_id_token,
        ):
            with patch("app.domain.auth.service.delete_firebase_user", mock_delete):
                from app.main import app

                with TestClient(app) as client:
                    reg = client.post(
                        "/api/v1/auth/register",
                        json={
                            "firebaseToken": reg_tok,
                            "name": "탈퇴테스트",
                            "birthDate": "1990-01-01",
                        },
                    )
                    assert reg.status_code == 200, reg.text
                    access = reg.json()["accessToken"]

                    wd = client.request(
                        "DELETE",
                        "/api/v1/auth/withdraw",
                        headers={"Authorization": f"Bearer {access}"},
                        json={"firebaseToken": reauth_tok},
                    )
                    assert wd.status_code == 200, wd.text
                    assert wd.json()["message"] == "계정이 삭제되었습니다."
                    mock_delete.assert_awaited_once()

                    again = client.post(
                        "/api/v1/auth/login",
                        json={"firebaseToken": reg_tok},
                    )
                    assert again.status_code == 404
                    assert again.json().get("code") == "USER_NOT_FOUND"
