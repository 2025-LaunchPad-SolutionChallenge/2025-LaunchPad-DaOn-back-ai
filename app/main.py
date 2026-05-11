from fastapi import FastAPI

from app.api.routes import router as api_router
from app.api.onboarding import router as onboarding_router

app = FastAPI(
    title="LaunchPad Backend",
    version="0.1.0",
)

app.include_router(api_router)
app.include_router(onboarding_router)


@app.get("/health", tags=["health"])
def health_check() -> dict[str, str]:
    return {"status": "ok"}
