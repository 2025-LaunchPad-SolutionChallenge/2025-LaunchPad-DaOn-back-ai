from fastapi import APIRouter
from pydantic import BaseModel

from app.infrastructure.batch.recovery_labeling import run_recovery_labeling_batch

router = APIRouter(prefix="/dev", tags=["dev"])


class BatchResponse(BaseModel):
    message: str


@router.post(
    "/batch/recovery",
    response_model=BatchResponse,
    summary="[DEV] 회복 라벨링 배치 수동 실행",
    description="매일 자정에 실행되는 회복 라벨링 배치를 즉시 실행합니다. 데모/테스트 전용입니다.",
)
async def trigger_recovery_batch() -> BatchResponse:
    await run_recovery_labeling_batch()
    return BatchResponse(message="회복 라벨링 배치 실행 완료")
