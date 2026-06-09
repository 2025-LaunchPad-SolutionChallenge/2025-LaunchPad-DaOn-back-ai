from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


class ChecklistCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str | None = None
    checklistDate: str | None = None
    priority: int = 1


class ChecklistPatchRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str | None = None
    checklistDate: str | None = None
    isCompleted: bool | None = None
    priority: int | None = None


class ChecklistMutationResponse(BaseModel):
    checklistItemId: int
    message: str


class AttachmentCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    attachmentType: str
    content: str | None = None
    fileUrl: str | None = None
    originalFileName: str | None = None
    mimeType: str | None = None
    fileSize: int | None = None
    thumbnailUrl: str | None = None


class AttachmentPatchRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    content: str | None = None
    fileUrl: str | None = None
    originalFileName: str | None = None
    mimeType: str | None = None
    fileSize: int | None = None
    thumbnailUrl: str | None = None


class AttachmentMutationResponse(BaseModel):
    attachmentId: int
    message: str


class ChecklistStatusResponse(BaseModel):
    checklistItemId: int
    isCompleted: bool
    completedAt: datetime | None
    message: str


class ChecklistDeleteResponse(BaseModel):
    checklistItemId: int
    deletedAttachments: int
    message: str


class ChecklistDetailAttachmentResponse(BaseModel):
    attachmentId: int
    attachmentType: str
    content: str | None
    fileUrl: str | None
    originalFileName: str | None
    mimeType: str | None
    fileSize: int | None
    thumbnailUrl: str | None
    createdAt: datetime


class ChecklistDetailResponse(BaseModel):
    checklistItemId: int
    title: str
    isCompleted: bool
    completedAt: datetime | None
    checklistDate: str
    priority: int
    isAiGenerated: bool
    attachments: list[ChecklistDetailAttachmentResponse]


class AttachmentSummary(BaseModel):
    MEMO: int
    IMAGE: int
    FILE: int


class ChecklistListItemResponse(BaseModel):
    checklistItemId: int
    title: str
    isCompleted: bool
    priority: int
    isAiGenerated: bool
    attachmentSummary: AttachmentSummary


class ChecklistListDayResponse(BaseModel):
    checklistDate: str
    total: int
    completed: int
    items: list[ChecklistListItemResponse]


class ChecklistRangeResponse(BaseModel):
    startDate: str
    endDate: str


class ChecklistListResponse(BaseModel):
    userDisasterId: int
    range: ChecklistRangeResponse
    completionRate: float
    days: list[ChecklistListDayResponse]


class ArchiveListItemResponse(BaseModel):
    attachmentId: int
    checklistItemId: int
    checklistItemTitle: str
    attachmentType: str
    fileUrl: str | None
    originalFileName: str | None
    mimeType: str | None
    thumbnailUrl: str | None
    checklistDate: str
    createdAt: datetime


class ArchiveListResponse(BaseModel):
    userDisasterId: int
    items: list[ArchiveListItemResponse]
    nextCursor: str | None
    hasMore: bool
