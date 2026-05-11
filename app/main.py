from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.common.exceptions import AppException
from app.config import settings
from app.firebase import init_firebase

# ── 라우터 import (도메인별로 추가) ──────────────
# from app.interface.auth.router import router as auth_router
from app.interface.user.router import router as user_router
# from app.interface.disaster.router import router as disaster_router
# from app.interface.home.router import router as home_router
# from app.interface.checklist.router import router as checklist_router
# from app.interface.community.router import router as community_router


@asynccontextmanager
async def lifespan(_app: FastAPI):
    init_firebase()
    yield


app = FastAPI(
    title=settings.APP_NAME,
    debug=settings.DEBUG,
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(AppException)
async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "code": exc.code,
            "message": exc.message,
            "data": None,
        },
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError,
) -> JSONResponse:
    errors = exc.errors()
    message = (
        errors[0].get("msg", "입력 값이 올바르지 않습니다.")
        if errors
        else "입력 값이 올바르지 않습니다."
    )
    return JSONResponse(
        status_code=422,
        content={
            "code": 422,
            "message": str(message),
            "data": None,
        },
    )


@app.exception_handler(StarletteHTTPException)
async def starlette_http_exception_handler(
    request: Request,
    exc: StarletteHTTPException,
) -> JSONResponse:
    detail = exc.detail
    if isinstance(detail, str):
        message = detail
    else:
        message = str(detail)
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "code": exc.status_code,
            "message": message,
            "data": None,
        },
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    return JSONResponse(
        status_code=500,
        content={
            "code": 500,
            "message": "서버 오류가 발생했습니다.",
            "data": None,
        },
    )


# app.include_router(auth_router, prefix="/api/v1")
app.include_router(user_router, prefix="/api/v1")
# app.include_router(disaster_router, prefix="/api/v1")
# app.include_router(home_router, prefix="/api/v1")
# app.include_router(checklist_router, prefix="/api/v1")
# app.include_router(community_router, prefix="/api/v1")


@app.get("/health", tags=["health"])
async def health_check() -> dict[str, str]:
    return {"status": "ok", "app": settings.APP_NAME}
