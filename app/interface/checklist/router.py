from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Any

from fastapi import APIRouter, Depends, Query

from app.common.dependencies import get_checklist_service, get_current_access_payload
from app.common.exceptions import AppException
from app.common.swagger import error_responses
from app.domain.checklist.service import ChecklistService
from app.interface.checklist.schema import (
    ArchiveListResponse,
    AttachmentCreateRequest,
    AttachmentMutationResponse,
    AttachmentPatchRequest,
    ChecklistContextRequest,
    ChecklistContextResponse,
    ChecklistGenerateRequest,
    ChecklistGenerateResponse,
    ChecklistStatusResponse,
    ChecklistCreateRequest,
    ChecklistDeleteResponse,
    ChecklistDetailAttachmentResponse,
    ChecklistDetailResponse,
    ChecklistListDayResponse,
    ChecklistListItemResponse,
    ChecklistListResponse,
    ChecklistMutationResponse,
    ChecklistPatchRequest,
    GeneratedItemInfo,
    WeeklyChecklistRateResponse,
)

router = APIRouter(tags=["checklists"])


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


def _parse_query_date_or_400(name: str, value: str | None) -> date | None:
    if value is None:
        return None
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError as exc:
        raise AppException(
            status_code=400,
            code=400,
            message=f"{name} 형식은 YYYY-MM-DD 이어야 합니다.",
            error_key="INVALID_DATE_FORMAT",
        ) from exc


@router.post(
    "/checklists/context",
    response_model=ChecklistContextResponse,
    summary="체크리스트 컨텍스트 업데이트",
    description="온보딩 시 생성된 재난 영향 정보의 외출 가능 여부/가용 시간을 업데이트합니다.",
    responses=error_responses(400, 401, 403, 404, 500),
)
async def submit_checklist_context(
    req: ChecklistContextRequest,
    payload: dict[str, Any] = Depends(get_current_access_payload),
    checklist_service: ChecklistService = Depends(get_checklist_service),
) -> ChecklistContextResponse:
    user_id = int(payload["sub"])
    await checklist_service.update_context(
        user_id=user_id,
        user_disaster_id=req.userDisasterId,
        can_go_out=req.userCondition.canGoOut,
        available_time=req.userCondition.availableTime,
        special_notes=req.userCondition.specialNotes,
    )
    return ChecklistContextResponse(message="상황 입력 완료")


@router.post(
    "/checklists/ai-generate",
    response_model=ChecklistGenerateResponse,
    summary="AI 체크리스트 생성",
    description="재난 영향 정보를 바탕으로 지정 날짜의 AI 체크리스트 3개를 생성합니다.",
    responses=error_responses(400, 401, 403, 404, 409, 500),
)
async def generate_ai_checklist(
    req: ChecklistGenerateRequest,
    payload: dict[str, Any] = Depends(get_current_access_payload),
    checklist_service: ChecklistService = Depends(get_checklist_service),
) -> ChecklistGenerateResponse:
    user_id = int(payload["sub"])
    generated = await checklist_service.generate_ai_checklist(
        user_id=user_id,
        user_disaster_id=req.userDisasterId,
        target_date=req.targetDate,
    )
    return ChecklistGenerateResponse(
        items=[
            GeneratedItemInfo(
                checklistItemId=item.checklist_item_id or 0,
                title=item.title,
                itemSourceType=item.item_source_type,
            )
            for item in generated
        ]
    )


@router.post(
    "/disasters/{userDisasterId}/checklist",
    response_model=ChecklistMutationResponse,
    status_code=201,
    summary="체크리스트 항목 추가",
    description="특정 재난에 수동 체크리스트 항목을 추가합니다. 기본 완료 상태는 false입니다.",
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


@router.get(
    "/disasters/{userDisasterId}/checklist/weekly-rate",
    response_model=WeeklyChecklistRateResponse,
    summary="주간 체크리스트 달성률 조회",
    description="이번 주(월~일) 기준 체크리스트 총 개수, 완료 개수, 달성률을 조회합니다.",
    responses=error_responses(401, 403, 404, 409, 500),
)
async def get_weekly_checklist_rate(
    userDisasterId: int,
    payload: dict[str, Any] = Depends(get_current_access_payload),
    checklist_service: ChecklistService = Depends(get_checklist_service),
) -> WeeklyChecklistRateResponse:
    user_id = int(payload["sub"])
    week_start, week_end, total_tasks, completed_tasks, completion_rate = (
        await checklist_service.get_weekly_completion_stats(
            user_id=user_id,
            user_disaster_id=userDisasterId,
        )
    )
    return WeeklyChecklistRateResponse(
        userDisasterId=userDisasterId,
        weekStartDate=week_start.isoformat(),
        weekEndDate=week_end.isoformat(),
        totalTasks=total_tasks,
        completedTasks=completed_tasks,
        weeklyCompletionRate=completion_rate,
    )


@router.patch(
    "/disasters/{userDisasterId}/checklist/{checklistItemId}",
    response_model=ChecklistMutationResponse,
    summary="체크리스트 항목 수정",
    description="체크리스트 제목/일자/우선순위/완료 여부를 부분 수정합니다.",
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
    "/disasters/{userDisasterId}/checklist/{checklistItemId}/attachments",
    response_model=AttachmentMutationResponse,
    status_code=201,
    summary="체크리스트 첨부 추가",
    description="체크리스트 항목에 메모/이미지/파일 첨부를 추가합니다.",
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
    "/disasters/{userDisasterId}/checklist/{checklistItemId}/attachments/{attachmentId}",
    response_model=AttachmentMutationResponse,
    summary="체크리스트 첨부 수정",
    description="첨부 본문 또는 파일 메타데이터를 부분 수정합니다.",
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
    "/disasters/{userDisasterId}/checklist/{checklistItemId}/attachments/{attachmentId}",
    response_model=AttachmentMutationResponse,
    summary="체크리스트 첨부 삭제",
    description="체크리스트 항목의 첨부를 삭제합니다.",
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


@router.patch(
    "/disasters/{userDisasterId}/checklist/{checklistItemId}/status",
    response_model=ChecklistStatusResponse,
    summary="체크리스트 완료 상태 변경",
    description="체크리스트 항목의 완료 상태를 변경합니다. true면 완료 시각을 기록합니다.",
    responses=error_responses(400, 401, 403, 404, 409, 500),
)
async def patch_checklist_status(
    userDisasterId: int,
    checklistItemId: int,
    req: dict[str, Any],
    payload: dict[str, Any] = Depends(get_current_access_payload),
    checklist_service: ChecklistService = Depends(get_checklist_service),
) -> ChecklistStatusResponse:
    user_id = int(payload["sub"])
    if "isCompleted" not in req:
        raise AppException(
            status_code=400,
            code=400,
            message="isCompleted가 필요합니다.",
            error_key="MISSING_REQUIRED_FIELD",
        )
    is_completed = req.get("isCompleted")
    if not isinstance(is_completed, bool):
        raise AppException(
            status_code=400,
            code=400,
            message="isCompleted는 boolean 이어야 합니다.",
            error_key="INVALID_FIELD_TYPE",
        )
    checklist_id, completed, completed_at = await checklist_service.patch_checklist_status(
        user_id=user_id,
        user_disaster_id=userDisasterId,
        checklist_item_id=checklistItemId,
        is_completed=is_completed,
    )
    return ChecklistStatusResponse(
        checklistItemId=checklist_id,
        isCompleted=completed,
        completedAt=completed_at,
        message="완료 상태가 변경되었습니다.",
    )


@router.delete(
    "/disasters/{userDisasterId}/checklist/{checklistItemId}",
    response_model=ChecklistDeleteResponse,
    summary="체크리스트 항목 삭제",
    description="체크리스트 항목과 해당 항목에 매핑된 첨부를 함께 삭제합니다.",
    responses=error_responses(401, 403, 404, 500),
)
async def delete_checklist(
    userDisasterId: int,
    checklistItemId: int,
    payload: dict[str, Any] = Depends(get_current_access_payload),
    checklist_service: ChecklistService = Depends(get_checklist_service),
) -> ChecklistDeleteResponse:
    user_id = int(payload["sub"])
    deleted_id, deleted_attachments = await checklist_service.delete_checklist_item(
        user_id=user_id,
        user_disaster_id=userDisasterId,
        checklist_item_id=checklistItemId,
    )
    return ChecklistDeleteResponse(
        checklistItemId=deleted_id,
        deletedAttachments=deleted_attachments,
        message="체크리스트 항목이 삭제되었습니다.",
    )


@router.get(
    "/disasters/{userDisasterId}/checklist/{checklistItemId}",
    response_model=ChecklistDetailResponse,
    summary="체크리스트 항목 상세 조회",
    description="체크리스트 항목 정보와 첨부 목록을 함께 조회합니다.",
    responses=error_responses(401, 403, 404, 500),
)
async def get_checklist_detail(
    userDisasterId: int,
    checklistItemId: int,
    payload: dict[str, Any] = Depends(get_current_access_payload),
    checklist_service: ChecklistService = Depends(get_checklist_service),
) -> ChecklistDetailResponse:
    user_id = int(payload["sub"])
    checklist, attachments = await checklist_service.get_checklist_detail(
        user_id=user_id,
        user_disaster_id=userDisasterId,
        checklist_item_id=checklistItemId,
    )
    return ChecklistDetailResponse(
        checklistItemId=int(checklist["checklistId"]),
        title=str(checklist["title"]),
        isCompleted=bool(checklist["isCompleted"]),
        completedAt=checklist["completedAt"],
        checklistDate=str(checklist["checklistDate"]),
        priority=int(checklist["priority"]),
        isAiGenerated=bool(checklist["isAiGenerated"]),
        attachments=[ChecklistDetailAttachmentResponse(**a) for a in attachments],
    )


@router.get(
    "/disasters/{userDisasterId}/checklist",
    response_model=ChecklistListResponse,
    summary="일자/기간 체크리스트 조회",
    description=(
        "date 단일 조회 또는 startDate/endDate 기간 조회를 지원합니다. "
        "기간 조회 시 날짜별 집계와 전체 달성률을 반환합니다."
    ),
    responses=error_responses(400, 401, 403, 404, 409, 500),
)
async def get_checklists(
    userDisasterId: int,
    date_value: str | None = Query(None, alias="date"),
    start_date_value: str | None = Query(None, alias="startDate"),
    end_date_value: str | None = Query(None, alias="endDate"),
    payload: dict[str, Any] = Depends(get_current_access_payload),
    checklist_service: ChecklistService = Depends(get_checklist_service),
) -> ChecklistListResponse:
    user_id = int(payload["sub"])
    parsed_date = _parse_query_date_or_400("date", date_value)
    parsed_start = _parse_query_date_or_400("startDate", start_date_value)
    parsed_end = _parse_query_date_or_400("endDate", end_date_value)
    resolved_start, resolved_end, rows = await checklist_service.get_checklists_by_date_range(
        user_id=user_id,
        user_disaster_id=userDisasterId,
        date_value=parsed_date,
        start_date=parsed_start,
        end_date=parsed_end,
    )

    rows_by_date: dict[str, list[dict[str, object]]] = {}
    for row in rows:
        key = str(row["checklistDate"])
        if key not in rows_by_date:
            rows_by_date[key] = []
        rows_by_date[key].append(row)

    days: list[ChecklistListDayResponse] = []
    total_count = 0
    completed_count = 0
    cursor = resolved_start
    while cursor <= resolved_end:
        key = cursor.isoformat()
        day_rows = rows_by_date.get(key, [])
        items = [
            ChecklistListItemResponse(
                checklistItemId=int(row["checklistItemId"]),
                title=str(row["title"]),
                isCompleted=bool(row["isCompleted"]),
                priority=int(row["priority"]),
                isAiGenerated=bool(row["isAiGenerated"]),
                attachmentSummary=row["attachmentSummary"],
            )
            for row in day_rows
        ]
        day_total = len(items)
        day_completed = sum(1 for row in items if row.isCompleted)
        total_count += day_total
        completed_count += day_completed
        days.append(
            ChecklistListDayResponse(
                checklistDate=key,
                total=day_total,
                completed=day_completed,
                items=items,
            )
        )
        cursor += timedelta(days=1)

    completion_rate = 0.0 if total_count == 0 else round((completed_count / total_count) * 100, 1)
    return ChecklistListResponse(
        userDisasterId=userDisasterId,
        range={
            "startDate": resolved_start.isoformat(),
            "endDate": resolved_end.isoformat(),
        },
        completionRate=completion_rate,
        days=days,
    )


@router.get(
    "/disasters/{userDisasterId}/archives",
    response_model=ArchiveListResponse,
    summary="아카이빙 통합 조회",
    description=(
        "ALL/MEMO/IMAGE/FILE 타입별 아카이브를 커서 기반으로 조회합니다. "
        "date를 주면 특정 일자만 필터링합니다."
    ),
    responses=error_responses(400, 401, 403, 404, 409, 500),
)
async def get_archives(
    userDisasterId: int,
    type_value: str = Query("ALL", alias="type"),
    date_value: str | None = Query(None, alias="date"),
    cursor: str | None = Query(None),
    limit: int = Query(20),
    payload: dict[str, Any] = Depends(get_current_access_payload),
    checklist_service: ChecklistService = Depends(get_checklist_service),
) -> ArchiveListResponse:
    user_id = int(payload["sub"])
    parsed_date = _parse_query_date_or_400("date", date_value)
    items, next_cursor, has_more = await checklist_service.get_archives(
        user_id=user_id,
        user_disaster_id=userDisasterId,
        archive_type=type_value,
        date_value=parsed_date,
        cursor=cursor,
        limit=limit,
    )
    return ArchiveListResponse(
        userDisasterId=userDisasterId,
        items=items,
        nextCursor=next_cursor,
        hasMore=has_more,
    )
