"""Firebase는 모킹하고, 실제 MySQL + Alembic 스키마로 인증 플로우를 검증."""

from __future__ import annotations

import hashlib
import secrets
from collections.abc import Generator, Sequence
from contextlib import ExitStack, contextmanager
from typing import Any
from unittest.mock import AsyncMock, patch

from sqlalchemy import create_engine, text
from starlette.testclient import TestClient

from firebase_admin.exceptions import UnauthenticatedError

from app.config import settings


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


def _sync_database_url() -> str:
    return settings.DATABASE_URL.replace("mysql+aiomysql://", "mysql+pymysql://", 1)


def _ensure_disaster_type(conn: Any, *, code: str, name: str) -> int:
    row = conn.execute(
        text("SELECT disaster_type_id FROM disaster_types WHERE disaster_code=:code"),
        {"code": code},
    ).first()
    if row is not None:
        return int(row[0])
    result = conn.execute(
        text(
            "INSERT INTO disaster_types (disaster_code, disaster_name, description) "
            "VALUES (:code, :name, NULL)"
        ),
        {"code": code, "name": name},
    )
    return int(result.lastrowid)


def _ensure_recovery_stage(conn: Any, *, code: str, name: str) -> int:
    row = conn.execute(
        text("SELECT recovery_stage_id FROM recovery_stage_masters WHERE stage_code=:code"),
        {"code": code},
    ).first()
    if row is not None:
        return int(row[0])
    result = conn.execute(
        text(
            "INSERT INTO recovery_stage_masters "
            "(stage_code, stage_name, description, created_at, updated_at) "
            "VALUES (:code, :name, NULL, NOW(), NOW())"
        ),
        {"code": code, "name": name},
    )
    return int(result.lastrowid)


def _seed_disaster_rows(user_id: int) -> dict[str, int]:
    engine = create_engine(_sync_database_url())
    try:
        with engine.begin() as conn:
            flood_type_id = _ensure_disaster_type(conn, code="FLOOD", name="홍수")
            fire_type_id = _ensure_disaster_type(conn, code="FIRE", name="화재")
            typhoon_type_id = _ensure_disaster_type(conn, code="TYPHOON", name="태풍")

            chaos_stage_id = _ensure_recovery_stage(conn, code="CHAOS", name="혼란기")
            stable_stage_id = _ensure_recovery_stage(conn, code="STABLE", name="안정기")
            recovery_stage_id = _ensure_recovery_stage(conn, code="RECOVERY", name="회복 유지기")

            active_id = int(
                conn.execute(
                    text(
                        "INSERT INTO user_disasters "
                        "(user_id, disaster_type_id, title, registered_at, ended_at, registration_status, "
                        "recovery_stage_id, recovery_progress, created_at, updated_at) "
                        "VALUES (:user_id, :type_id, :title, :registered_at, NULL, 'ACTIVE', :stage_id, :progress, NOW(), NOW())"
                    ),
                    {
                        "user_id": user_id,
                        "type_id": flood_type_id,
                        "title": "2026 여름 침수 피해",
                        "registered_at": "2026-07-15 14:00:00",
                        "stage_id": chaos_stage_id,
                        "progress": 0.15,
                    },
                ).lastrowid
            )
            expired_id = int(
                conn.execute(
                    text(
                        "INSERT INTO user_disasters "
                        "(user_id, disaster_type_id, title, registered_at, ended_at, registration_status, "
                        "recovery_stage_id, recovery_progress, created_at, updated_at) "
                        "VALUES (:user_id, :type_id, :title, :registered_at, :ended_at, 'EXPIRED', :stage_id, :progress, NOW(), NOW())"
                    ),
                    {
                        "user_id": user_id,
                        "type_id": fire_type_id,
                        "title": "2026 봄 산불",
                        "registered_at": "2026-03-10 09:00:00",
                        "ended_at": "2026-03-15 18:00:00",
                        "stage_id": stable_stage_id,
                        "progress": 0.82,
                    },
                ).lastrowid
            )
            archived_id = int(
                conn.execute(
                    text(
                        "INSERT INTO user_disasters "
                        "(user_id, disaster_type_id, title, registered_at, ended_at, registration_status, "
                        "recovery_stage_id, recovery_progress, created_at, updated_at) "
                        "VALUES (:user_id, :type_id, :title, :registered_at, :ended_at, 'ARCHIVED', :stage_id, :progress, NOW(), NOW())"
                    ),
                    {
                        "user_id": user_id,
                        "type_id": typhoon_type_id,
                        "title": "2025 태풍",
                        "registered_at": "2025-09-01 00:00:00",
                        "ended_at": "2025-09-03 00:00:00",
                        "stage_id": recovery_stage_id,
                        "progress": 1.0,
                    },
                ).lastrowid
            )

            impact_id = int(
                conn.execute(
                    text(
                        "INSERT INTO disaster_impacts "
                        "(user__disaster_id, safety_status, residence_status, injury_level, "
                        "can_go_out, available_time, created_at, updated_at) "
                        "VALUES (:user_disaster_id, 'DAMAGED', 'PARTIAL_DAMAGE', 'MINOR', 0, "
                        "'UNDER_ONE_HOUR', NOW(), NOW())"
                    ),
                    {"user_disaster_id": active_id},
                ).lastrowid
            )
            conn.execute(
                text(
                    "INSERT INTO flood_impacts "
                    "(flood_level, water_drain_status, damage_house, damage_vehicle, "
                    "electric_problem, water_problem, impact_id) "
                    "VALUES ('FIRST_FLOOR', 'PARTIAL_DRAINED', 1, 0, 1, 1, :impact_id)"
                ),
                {"impact_id": impact_id},
            )

            return {"active": active_id, "expired": expired_id, "archived": archived_id}
    finally:
        engine.dispose()


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


def test_disaster_list_detail_patch_and_close_flow() -> None:
    token = "firebase-ok-disaster-" + secrets.token_hex(6)
    with _test_client() as client:
        reg = client.post(
            "/api/v1/auth/register",
            json={
                "firebaseToken": token,
                "name": "재난테스트",
                "birthDate": "1991-05-05",
            },
        )
        assert reg.status_code == 200, reg.text
        access = reg.json()["accessToken"]
        me = client.get("/api/v1/users/me", headers={"Authorization": f"Bearer {access}"})
        user_id = int(me.json()["userId"])

        ids = _seed_disaster_rows(user_id)

        listed = client.get(
            "/api/v1/disasters?page=0&size=20",
            headers={"Authorization": f"Bearer {access}"},
        )
        assert listed.status_code == 200, listed.text
        body = listed.json()
        assert body["totalElements"] >= 3
        first_three = body["content"][:3]
        assert [x["status"] for x in first_three] == ["ACTIVE", "EXPIRED", "ARCHIVED"]
        assert first_three[0]["disasterTypeCode"] == "FLOOD"

        detail = client.get(
            f"/api/v1/disasters/{ids['active']}",
            headers={"Authorization": f"Bearer {access}"},
        )
        assert detail.status_code == 200, detail.text
        d = detail.json()
        assert d["impact"]["safetyStatus"] == "DAMAGED"
        assert d["detail"]["floodLevel"] == "FIRST_FLOOR"

        patch_resp = client.patch(
            f"/api/v1/disasters/{ids['active']}",
            headers={"Authorization": f"Bearer {access}"},
            json={
                "title": "2026 여름 침수 피해 (수정)",
                "impact": {
                    "safetyStatus": "SAFE",
                    "residenceStatus": "LIVABLE",
                    "injuryLevel": "NONE",
                    "canGoOut": True,
                    "availableTime": "ALL_DAY_HALF_DAY",
                },
                "detail": {
                    "floodLevel": "NONE",
                    "waterDrainStatus": "MOSTLY_DRAINED",
                    "damageHouse": False,
                    "damageVehicle": False,
                    "electricProblem": False,
                    "waterProblem": False,
                },
            },
        )
        assert patch_resp.status_code == 200, patch_resp.text
        assert patch_resp.json()["message"] == "재난 정보가 수정되었습니다."

        patched_detail = client.get(
            f"/api/v1/disasters/{ids['active']}",
            headers={"Authorization": f"Bearer {access}"},
        ).json()
        assert patched_detail["title"] == "2026 여름 침수 피해 (수정)"
        assert patched_detail["impact"]["safetyStatus"] == "SAFE"
        assert patched_detail["detail"]["waterDrainStatus"] == "MOSTLY_DRAINED"

        close_resp = client.patch(
            f"/api/v1/disasters/{ids['active']}/close",
            headers={"Authorization": f"Bearer {access}"},
            json={"action": "CLOSE"},
        )
        assert close_resp.status_code == 200, close_resp.text
        closed = close_resp.json()
        assert closed["status"] == "EXPIRED"
        assert closed["endedAt"] is not None

        lock_edit = client.patch(
            f"/api/v1/disasters/{ids['active']}",
            headers={"Authorization": f"Bearer {access}"},
            json={"title": "수정불가"},
        )
        assert lock_edit.status_code == 409, lock_edit.text
        assert lock_edit.json()["code"] == "DISASTER_NOT_EDITABLE"


def test_disaster_forbidden_and_not_found_errors() -> None:
    owner_token = "firebase-ok-disaster-owner-" + secrets.token_hex(6)
    other_token = "firebase-ok-disaster-other-" + secrets.token_hex(6)

    with _test_client() as client:
        owner = client.post(
            "/api/v1/auth/register",
            json={
                "firebaseToken": owner_token,
                "name": "소유자",
                "birthDate": "1990-01-01",
            },
        )
        assert owner.status_code == 200, owner.text
        owner_access = owner.json()["accessToken"]
        owner_me = client.get("/api/v1/users/me", headers={"Authorization": f"Bearer {owner_access}"})
        owner_id = int(owner_me.json()["userId"])
        ids = _seed_disaster_rows(owner_id)

        other = client.post(
            "/api/v1/auth/register",
            json={
                "firebaseToken": other_token,
                "name": "타인",
                "birthDate": "1992-02-02",
            },
        )
        assert other.status_code == 200, other.text
        other_access = other.json()["accessToken"]

        forbidden = client.get(
            f"/api/v1/disasters/{ids['active']}",
            headers={"Authorization": f"Bearer {other_access}"},
        )
        assert forbidden.status_code == 403, forbidden.text
        assert forbidden.json()["code"] == "FORBIDDEN"

        not_found = client.get(
            "/api/v1/disasters/999999999",
            headers={"Authorization": f"Bearer {owner_access}"},
        )
        assert not_found.status_code == 404, not_found.text
        assert not_found.json()["code"] == "DISASTER_NOT_FOUND"
