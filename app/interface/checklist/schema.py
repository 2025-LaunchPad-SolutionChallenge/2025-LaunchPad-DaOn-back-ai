from __future__ import annotations

from enum import Enum
from datetime import datetime
from datetime import date

from pydantic import BaseModel, ConfigDict, Field


class ChecklistCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str | None = Field(default=None, description="체크리스트 제목")
    checklistDate: str | None = Field(default=None, description="체크리스트 일자(yyyy-MM-dd)")
    priority: int = Field(default=1, description="우선순위")


class ChecklistPatchRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str | None = Field(default=None, description="체크리스트 제목")
    checklistDate: str | None = Field(default=None, description="체크리스트 일자(yyyy-MM-dd)")
    isCompleted: bool | None = Field(default=None, description="완료 여부")
    priority: int | None = Field(default=None, description="우선순위")


class ChecklistMutationResponse(BaseModel):
    checklistItemId: int = Field(..., description="체크리스트 항목 ID")
    message: str = Field(..., description="처리 결과 메시지")


class AttachmentCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    attachmentType: str = Field(..., description="첨부 타입(MEMO/IMAGE/FILE)")
    content: str | None = Field(default=None, description="메모 본문(MEMO 타입)")
    fileUrl: str | None = Field(default=None, description="파일 URL(IMAGE/FILE 타입)")
    originalFileName: str | None = Field(default=None, description="원본 파일명")
    mimeType: str | None = Field(default=None, description="MIME 타입")
    fileSize: int | None = Field(default=None, description="파일 크기(byte)")
    thumbnailUrl: str | None = Field(default=None, description="썸네일 URL")


class AttachmentPatchRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    content: str | None = Field(default=None, description="메모 본문")
    fileUrl: str | None = Field(default=None, description="파일 URL")
    originalFileName: str | None = Field(default=None, description="원본 파일명")
    mimeType: str | None = Field(default=None, description="MIME 타입")
    fileSize: int | None = Field(default=None, description="파일 크기(byte)")
    thumbnailUrl: str | None = Field(default=None, description="썸네일 URL")


class AttachmentMutationResponse(BaseModel):
    attachmentId: int = Field(..., description="첨부 ID")
    message: str = Field(..., description="처리 결과 메시지")


class ChecklistStatusResponse(BaseModel):
    checklistItemId: int = Field(..., description="체크리스트 항목 ID")
    isCompleted: bool = Field(..., description="완료 여부")
    completedAt: datetime | None = Field(..., description="완료 시각(미완료면 null)")
    message: str = Field(..., description="처리 결과 메시지")


class ChecklistDeleteResponse(BaseModel):
    checklistItemId: int = Field(..., description="삭제된 체크리스트 항목 ID")
    deletedAttachments: int = Field(..., description="함께 삭제된 첨부 개수")
    message: str = Field(..., description="처리 결과 메시지")


class ChecklistDetailAttachmentResponse(BaseModel):
    attachmentId: int = Field(..., description="첨부 ID")
    attachmentType: str = Field(..., description="첨부 타입(MEMO/IMAGE/FILE)")
    content: str | None = Field(default=None, description="메모 본문")
    fileUrl: str | None = Field(default=None, description="파일 URL")
    originalFileName: str | None = Field(default=None, description="원본 파일명")
    mimeType: str | None = Field(default=None, description="MIME 타입")
    fileSize: int | None = Field(default=None, description="파일 크기(byte)")
    thumbnailUrl: str | None = Field(default=None, description="썸네일 URL")
    createdAt: datetime = Field(..., description="첨부 생성 시각")


class ChecklistDetailResponse(BaseModel):
    checklistItemId: int = Field(..., description="체크리스트 항목 ID")
    title: str = Field(..., description="체크리스트 제목")
    isCompleted: bool = Field(..., description="완료 여부")
    completedAt: datetime | None = Field(..., description="완료 시각")
    checklistDate: str = Field(..., description="체크리스트 일자(yyyy-MM-dd)")
    priority: int = Field(..., description="우선순위")
    isAiGenerated: bool = Field(..., description="AI 생성 항목 여부")
    attachments: list[ChecklistDetailAttachmentResponse] = Field(..., description="첨부 목록")


class AttachmentSummary(BaseModel):
    MEMO: int = Field(..., description="메모 첨부 개수")
    IMAGE: int = Field(..., description="이미지 첨부 개수")
    FILE: int = Field(..., description="파일 첨부 개수")


class ChecklistListItemResponse(BaseModel):
    checklistItemId: int = Field(..., description="체크리스트 항목 ID")
    title: str = Field(..., description="체크리스트 제목")
    isCompleted: bool = Field(..., description="완료 여부")
    priority: int = Field(..., description="우선순위")
    isAiGenerated: bool = Field(..., description="AI 생성 항목 여부")
    attachmentSummary: AttachmentSummary = Field(..., description="첨부 타입별 개수")


class ChecklistListDayResponse(BaseModel):
    checklistDate: str = Field(..., description="조회 일자(yyyy-MM-dd)")
    total: int = Field(..., description="해당 일자의 총 체크리스트 개수")
    completed: int = Field(..., description="해당 일자의 완료 개수")
    items: list[ChecklistListItemResponse] = Field(..., description="해당 일자 체크리스트 목록")


class ChecklistRangeResponse(BaseModel):
    startDate: str = Field(..., description="조회 시작일(yyyy-MM-dd)")
    endDate: str = Field(..., description="조회 종료일(yyyy-MM-dd)")


class ChecklistListResponse(BaseModel):
    userDisasterId: int = Field(..., description="재난 ID")
    range: ChecklistRangeResponse = Field(..., description="조회 범위")
    completionRate: float = Field(..., description="범위 내 전체 달성률(%)")
    days: list[ChecklistListDayResponse] = Field(..., description="날짜별 집계 목록")


class ArchiveListItemResponse(BaseModel):
    attachmentId: int = Field(..., description="첨부 ID")
    checklistItemId: int = Field(..., description="체크리스트 항목 ID")
    checklistItemTitle: str = Field(..., description="체크리스트 항목 제목")
    attachmentType: str = Field(..., description="첨부 타입(MEMO/IMAGE/FILE)")
    fileUrl: str | None = Field(default=None, description="파일 URL")
    originalFileName: str | None = Field(default=None, description="원본 파일명")
    mimeType: str | None = Field(default=None, description="MIME 타입")
    thumbnailUrl: str | None = Field(default=None, description="썸네일 URL")
    checklistDate: str = Field(..., description="체크리스트 일자(yyyy-MM-dd)")
    createdAt: datetime = Field(..., description="첨부 생성 시각")


class ArchiveListResponse(BaseModel):
    userDisasterId: int = Field(..., description="재난 ID")
    items: list[ArchiveListItemResponse] = Field(..., description="아카이브 아이템 목록")
    nextCursor: str | None = Field(default=None, description="다음 페이지 커서")
    hasMore: bool = Field(..., description="다음 페이지 존재 여부")


class ChecklistGenerateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    userDisasterId: int = Field(..., description="재난 ID")
    targetDate: date = Field(..., description="생성 대상 날짜")


class GeneratedItemInfo(BaseModel):
    checklistItemId: int = Field(..., description="생성된 체크리스트 항목 ID")
    title: str = Field(..., description="생성된 할 일 제목")
    itemSourceType: str = Field(..., description="항목 출처 타입")


class ChecklistGenerateResponse(BaseModel):
    items: list[GeneratedItemInfo] = Field(..., description="생성된 체크리스트 목록")


class AvailableTimeEnum(str, Enum):
    UNDER_ONE_HOUR = "UNDER_ONE_HOUR"
    ONE_TO_THREE_HOURS = "ONE_TO_THREE_HOURS"
    ALL_DAY_HALF_DAY = "ALL_DAY_HALF_DAY"


class ContextUserConditionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    canGoOut: bool = Field(..., description="외출 가능 여부")
    availableTime: AvailableTimeEnum = Field(..., description="가용 시간")


class ChecklistContextRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    userDisasterId: int = Field(..., description="재난 ID")
    userCondition: ContextUserConditionRequest = Field(..., description="사용자 상태")


class ChecklistContextResponse(BaseModel):
    message: str = Field(..., description="처리 결과 메시지")
