"""OpenAPI(Swagger) 공통 설정 및 재사용 스키마."""

from typing import Any

from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi
from pydantic import BaseModel, ConfigDict, Field

OPENAPI_TAGS: list[dict[str, str]] = [
    {
        "name": "auth",
        "description": "Firebase 기반 회원가입·로그인, JWT 발급·갱신·로그아웃, 회원탈퇴",
    },
    {
        "name": "users",
        "description": "인증된 사용자의 프로필 조회·수정 및 프로필 이미지 업로드",
    },
    {
        "name": "disasters",
        "description": "재난 목록 조회, 상세 조회, 수정, 종료/보관 처리",
    },
    {
        "name": "health",
        "description": "서버 상태 확인",
    },
]


class ErrorResponse(BaseModel):
    """API 공통 에러 응답 (code, message, data)."""

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "code": "UNAUTHORIZED",
                    "message": "액세스 토큰이 유효하지 않습니다.",
                    "data": None,
                }
            ]
        }
    )

    code: str | int = Field(..., description="에러 코드 (문자열 키 또는 HTTP 상태 코드)")
    message: str = Field(..., description="에러 메시지")
    data: None = Field(default=None, description="에러 시 항상 null")


def _error_response(status_code: int, description: str) -> dict[str, Any]:
    return {
        "description": description,
        "content": {
            "application/json": {
                "schema": ErrorResponse.model_json_schema(),
            }
        },
    }


COMMON_ERROR_RESPONSES: dict[int | str, dict[str, Any]] = {
    400: _error_response(400, "잘못된 요청 (필수 필드 누락, 형식 오류 등)"),
    401: _error_response(401, "인증 실패 (토큰 없음, 만료, 유효하지 않음)"),
    403: _error_response(403, "접근 권한 없음"),
    404: _error_response(404, "리소스를 찾을 수 없음"),
    409: _error_response(409, "리소스 충돌 (중복 등)"),
    422: _error_response(422, "요청 본문 검증 실패"),
    500: _error_response(500, "서버 내부 오류"),
}


def error_responses(*status_codes: int) -> dict[int | str, dict[str, Any]]:
    return {code: COMMON_ERROR_RESPONSES[code] for code in status_codes}


def configure_openapi(app: FastAPI) -> None:
    """Bearer JWT 보안 스키마를 포함한 OpenAPI 스키마를 등록합니다."""

    def custom_openapi() -> dict[str, Any]:
        if app.openapi_schema:
            return app.openapi_schema

        schema = get_openapi(
            title=app.title,
            version=app.version,
            description=app.description,
            routes=app.routes,
            tags=app.openapi_tags,
        )
        components = schema.setdefault("components", {})
        security_schemes = components.setdefault("securitySchemes", {})
        security_schemes["BearerAuth"] = {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
            "description": "로그인/회원가입 응답의 accessToken을 Bearer 토큰으로 전달",
        }
        app.openapi_schema = schema
        return app.openapi_schema

    app.openapi = custom_openapi  # type: ignore[method-assign]
