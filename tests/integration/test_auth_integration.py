"""Firebase는 모킹하고, 실제 MySQL + Alembic 스키마로 인증 플로우를 검증."""

from __future__ import annotations

import hashlib
import secrets
from collections.abc import Generator, Sequence
from contextlib import ExitStack, contextmanager
from typing import Any
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
def _test_client(
    extra_patches: Sequence[Any] | None = None,
) -> Generator[TestClient, None, None]:
    with patch("app.main.init_firebase", lambda: None):
        with patch(
            "app.domain.auth.service.verify_firebase_id_token",
            side_effect=_fake_verify_firebase_id_token,
        ):
            with ExitStack() as stack:
                for p in extra_patches or []:
                    stack.enter_context(p)
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
        assert payload.get("userId") >= 1
        assert payload.get("name") == "통합테스트"
        assert payload.get("birthDate") == "1995-03-15"
        assert payload.get("residenceVerified") is False

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
    with _test_client(
        [patch("app.domain.auth.service.delete_firebase_user", mock_delete)],
    ) as client:
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
        refresh = reg.json()["refreshToken"]

        wd = client.request(
            "DELETE",
            "/api/v1/auth/withdraw",
            headers={"Authorization": f"Bearer {access}"},
        )
        assert wd.status_code == 200, wd.text
        assert wd.json()["message"] == "계정이 삭제되었습니다."
        mock_delete.assert_awaited_once()

        # 탈퇴 시 해당 유저의 refresh 세션도 서버에서 무효화된다.
        revoked = client.post(
            "/api/v1/auth/refresh",
            json={"refreshToken": refresh},
        )
        assert revoked.status_code == 401
        assert revoked.json().get("code") == "REVOKED_REFRESH_TOKEN"

        again = client.post(
            "/api/v1/auth/login",
            json={"firebaseToken": reg_tok},
        )
        assert again.status_code == 404
        assert again.json().get("code") == "USER_NOT_FOUND"


def test_register_duplicate_uid_409() -> None:
    """같은 Firebase UID로 두 번 가입 시도 → 409."""
    token = "firebase-ok-dup-" + secrets.token_hex(6)
    with _test_client() as client:
        first = client.post(
            "/api/v1/auth/register",
            json={
                "firebaseToken": token,
                "name": "첫가입",
                "birthDate": "1995-01-01",
            },
        )
        assert first.status_code == 200, first.text

        second = client.post(
            "/api/v1/auth/register",
            json={
                "firebaseToken": token,
                "name": "둘째시도",
                "birthDate": "1996-06-06",
            },
        )
        assert second.status_code == 409, second.text
        assert second.json().get("code") == "DUPLICATE_FIREBASE_USER"


def test_register_missing_fields_400() -> None:
    """필수 필드 누락 → 400 VALIDATION_ERROR."""
    with _test_client() as client:
        r = client.post("/api/v1/auth/register", json={})
        assert r.status_code == 400, r.text
        assert r.json().get("code") == "VALIDATION_ERROR"


def _firebase_storage_url(filename: str = "avatar.png") -> str:
    return (
        "https://firebasestorage.googleapis.com/v0/b/test-project.appspot.com/o/"
        f"profile-images%2F{filename}?alt=media&token=mock"
    )


def test_user_profile_update_and_upload_flow() -> None:
    token = "firebase-ok-profile-" + secrets.token_hex(6)
    profile_url = _firebase_storage_url("avatar.png")
    with _test_client() as client:
        reg = client.post(
            "/api/v1/auth/register",
            json={
                "firebaseToken": token,
                "name": "프로필테스트",
                "birthDate": "1994-07-21",
            },
        )
        assert reg.status_code == 200, reg.text
        access = reg.json()["accessToken"]

        update = client.put(
            "/api/v1/users/me",
            headers={"Authorization": f"Bearer {access}"},
            data={
                "nickname": "kate",
                "addressName": "서울 강남구 역삼1동",
                "householdType": "SINGLE",
                "profileImageUrl": profile_url,
            },
        )
        assert update.status_code == 200, update.text
        assert update.json()["message"] == "프로필이 수정되었습니다"

        me = client.get(
            "/api/v1/users/me",
            headers={"Authorization": f"Bearer {access}"},
        )
        assert me.status_code == 200, me.text
        profile = me.json()
        assert profile["nickname"] == "kate"
        assert profile["addressName"] == "서울 강남구 역삼1동"
        assert profile["profileImage"] == profile_url
        assert profile["residenceVerified"] is False

        webp_url = _firebase_storage_url("avatar.webp")
        image_upload = client.post(
            "/api/v1/users/me/profile-image",
            headers={"Authorization": f"Bearer {access}"},
            json={"profileImageUrl": webp_url},
        )
        assert image_upload.status_code == 200, image_upload.text
        assert image_upload.json()["profileImageUrl"] == webp_url


def test_user_profile_image_upload_validation_errors() -> None:
    token = "firebase-ok-profile-invalid-" + secrets.token_hex(6)
    with _test_client() as client:
        reg = client.post(
            "/api/v1/auth/register",
            json={"firebaseToken": token, "name": "파일검증", "birthDate": "1991-01-01"},
        )
        assert reg.status_code == 200, reg.text
        access = reg.json()["accessToken"]

        missing = client.post(
            "/api/v1/users/me/profile-image",
            headers={"Authorization": f"Bearer {access}"},
            json={},
        )
        assert missing.status_code == 400, missing.text
        assert missing.json()["code"] == "MISSING_PROFILE_IMAGE_URL"

        bad_type = client.post(
            "/api/v1/users/me/profile-image",
            headers={"Authorization": f"Bearer {access}"},
            json={"profileImageUrl": _firebase_storage_url("avatar.gif")},
        )
        assert bad_type.status_code == 400, bad_type.text
        assert bad_type.json()["code"] == "UNSUPPORTED_FILE_TYPE"

        bad_host = client.post(
            "/api/v1/users/me/profile-image",
            headers={"Authorization": f"Bearer {access}"},
            json={"profileImageUrl": "https://example.com/avatar.png"},
        )
        assert bad_host.status_code == 400, bad_host.text
        assert bad_host.json()["code"] == "INVALID_PROFILE_IMAGE_URL"


def test_refresh_with_old_token_after_rotate() -> None:
    """refresh로 새 토큰 발급 후, 이전 refresh token 재사용 → 401 REVOKED."""
    token = "firebase-ok-rotate-" + secrets.token_hex(6)
    with _test_client() as client:
        reg = client.post(
            "/api/v1/auth/register",
            json={
                "firebaseToken": token,
                "name": "회전테스트",
                "birthDate": "1992-02-02",
            },
        )
        assert reg.status_code == 200, reg.text
        old_refresh = reg.json()["refreshToken"]

        ref = client.post(
            "/api/v1/auth/refresh",
            json={"refreshToken": old_refresh},
        )
        assert ref.status_code == 200, ref.text
        assert ref.json()["refreshToken"] != old_refresh

        stale = client.post(
            "/api/v1/auth/refresh",
            json={"refreshToken": old_refresh},
        )
        assert stale.status_code == 401, stale.text
        assert stale.json().get("code") == "REVOKED_REFRESH_TOKEN"
