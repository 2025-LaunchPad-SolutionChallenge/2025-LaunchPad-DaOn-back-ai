from __future__ import annotations

from datetime import date, datetime
from typing import Any

from fastapi import APIRouter, Depends

from app.common.dependencies import get_checklist_service, get_current_access_payload
from app.common.exceptions import AppException
from app.common.swagger import error_responses
from app.domain.checklist.service import ChecklistService
from app.interface.checklist.schema import (
    AttachmentCreateRequest,
    AttachmentMutationResponse,
    AttachmentPatchRequest,
    ChecklistCreateRequest,
    ChecklistMutationResponse,
    ChecklistPatchRequest,
)

router = APIRouter(prefix="/disasters", tags=["checklists"])


def _parse_iso_date_or_400(value: str) -> date:
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError as exc:
        raise AppException(
            status_code=400,
            code=400,
            message="checklistDate 형식은 yyyy-MM-dd 이어야 합니다.",
            error_key="INVALID_DATE_FORMAT",
        ) from exc


@router.post(
    "/{userDisasterId}/checklist",
    response_model=ChecklistMutationResponse,
    status_code=201,
    summary="체크리스트 항목 추가",
    responses=error_responses(400, 401, 403, 404, 409, 500),
)
async def create_checklist_item(
    userDisasterId: int,
    req: ChecklistCreateRequest,
    payload: dict[str, Any] = Depends(get_current_access_payload),
    checklist_service: ChecklistService = Depends(get_checklist_service),
) -> ChecklistMutationResponse:
    user_id = int(payload["sub"])
    checklist_date = _parse_iso_date_or_400(req.checklistDate)
    item_id = await checklist_service.add_checklist_item(
        user_id=user_id,
        user_disaster_id=userDisasterId,
        title=req.title,
        checklist_date=checklist_date,
        priority=req.priority,
    )
    return ChecklistMutationResponse(
        checklistItemId=item_id,
        message="체크리스트 항목이 추가되었습니다.",
    )


@router.patch(
    "/{userDisasterId}/checklist/{checklistItemId}",
    response_model=ChecklistMutationResponse,
    summary="체크리스트 항목 수정",
    responses=error_responses(400, 401, 403, 404, 409, 500),
)
async def patch_checklist_item(
    userDisasterId: int,
    checklistItemId: int,
    req: ChecklistPatchRequest,
    payload: dict[str, Any] = Depends(get_current_access_payload),
    checklist_service: ChecklistService = Depends(get_checklist_service),
) -> ChecklistMutationResponse:
    user_id = int(payload["sub"])
    has_any_field = any(
        value is not None
        for value in (req.title, req.checklistDate, req.isCompleted, req.priority)
    )
    checklist_date = _parse_iso_date_or_400(req.checklistDate) if req.checklistDate else None
    item_id = await checklist_service.patch_checklist_item(
        user_id=user_id,
        user_disaster_id=userDisasterId,
        checklist_item_id=checklistItemId,
        title=req.title,
        checklist_date=checklist_date,
        is_completed=req.isCompleted,
        priority=req.priority,
        has_any_field=has_any_field,
    )
    return ChecklistMutationResponse(
        checklistItemId=item_id,
        message="체크리스트 항목이 수정되었습니다.",
    )


@router.post(
    "/{userDisasterId}/checklist/{checklistItemId}/attachments",
    response_model=AttachmentMutationResponse,
    status_code=201,
    summary="체크리스트 첨부 추가",
    responses=error_responses(400, 401, 403, 404, 409, 500),
)
async def create_attachment(
    userDisasterId: int,
    checklistItemId: int,
    req: AttachmentCreateRequest,
    payload: dict[str, Any] = Depends(get_current_access_payload),
    checklist_service: ChecklistService = Depends(get_checklist_service),
) -> AttachmentMutationResponse:
    user_id = int(payload["sub"])
    attachment_id = await checklist_service.add_attachment(
        user_id=user_id,
        user_disaster_id=userDisasterId,
        checklist_item_id=checklistItemId,
        attachment_type=req.attachmentType,
        content=req.content,
        file_url=req.fileUrl,
        original_file_name=req.originalFileName,
        mime_type=req.mimeType,
        file_size=req.fileSize,
        thumbnail_url=req.thumbnailUrl,
    )
    return AttachmentMutationResponse(
        attachmentId=attachment_id,
        message="첨부가 추가되었습니다.",
    )


@router.patch(
    "/{userDisasterId}/checklist/{checklistItemId}/attachments/{attachmentId}",
    response_model=AttachmentMutationResponse,
    summary="체크리스트 첨부 수정",
    responses=error_responses(400, 401, 403, 404, 409, 500),
)
async def patch_attachment(
    userDisasterId: int,
    checklistItemId: int,
    attachmentId: int,
    req: AttachmentPatchRequest,
    payload: dict[str, Any] = Depends(get_current_access_payload),
    checklist_service: ChecklistService = Depends(get_checklist_service),
) -> AttachmentMutationResponse:
    user_id = int(payload["sub"])
    has_any_field = any(
        value is not None
        for value in (
            req.content,
            req.fileUrl,
            req.originalFileName,
            req.mimeType,
            req.fileSize,
            req.thumbnailUrl,
        )
    )
    attachment_id = await checklist_service.patch_attachment(
        user_id=user_id,
        user_disaster_id=userDisasterId,
        checklist_item_id=checklistItemId,
        attachment_id=attachmentId,
        content=req.content,
        file_url=req.fileUrl,
        original_file_name=req.originalFileName,
        mime_type=req.mimeType,
        file_size=req.fileSize,
        thumbnail_url=req.thumbnailUrl,
        has_any_field=has_any_field,
    )
    return AttachmentMutationResponse(
        attachmentId=attachment_id,
        message="첨부가 수정되었습니다.",
    )


@router.delete(
    "/{userDisasterId}/checklist/{checklistItemId}/attachments/{attachmentId}",
    response_model=AttachmentMutationResponse,
    summary="체크리스트 첨부 삭제",
    responses=error_responses(401, 403, 404, 409, 500),
)
async def delete_attachment(
    userDisasterId: int,
    checklistItemId: int,
    attachmentId: int,
    payload: dict[str, Any] = Depends(get_current_access_payload),
    checklist_service: ChecklistService = Depends(get_checklist_service),
) -> AttachmentMutationResponse:
    user_id = int(payload["sub"])
    deleted = await checklist_service.delete_attachment(
        user_id=user_id,
        user_disaster_id=userDisasterId,
        checklist_item_id=checklistItemId,
        attachment_id=attachmentId,
    )
    return AttachmentMutationResponse(
        attachmentId=deleted,
        message="첨부가 삭제되었습니다.",
    )
