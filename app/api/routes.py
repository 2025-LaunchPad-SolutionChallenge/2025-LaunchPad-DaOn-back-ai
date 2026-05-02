from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.crud.user import create_user, get_user_by_email, list_users
from app.db.session import get_db
from app.schemas.user import UserCreate, UserRead

router = APIRouter(prefix="/api")


@router.get("/users", response_model=list[UserRead], tags=["users"])
def get_users(db: Session = Depends(get_db)) -> list[UserRead]:
    return list_users(db)


@router.post("/users", response_model=UserRead, tags=["users"])
def post_user(payload: UserCreate, db: Session = Depends(get_db)) -> UserRead:
    if get_user_by_email(db, payload.email):
        raise HTTPException(status_code=400, detail="Email already exists")
    return create_user(db, payload)
