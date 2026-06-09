from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class ChecklistCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str
    checklistDate: str
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
