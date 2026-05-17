"""JWT 액세스 토큰 기준 현재 요청 사용자 클레임."""

from app.common.dependencies import get_current_access_payload

get_current_user = get_current_access_payload

__all__ = ["get_current_user"]
