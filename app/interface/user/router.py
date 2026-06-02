from typing import Any

from fastapi import APIRouter, Depends

from app.common.security import get_current_user

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me")
async def get_me(current_user: dict[str, Any] = Depends(get_current_user)) -> dict[str, Any]:
    return current_user
