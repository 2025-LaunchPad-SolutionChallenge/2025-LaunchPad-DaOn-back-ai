from __future__ import annotations

from datetime import date
from urllib.parse import urlparse

from app.common.exceptions import AppException
from app.domain.checklist.repository import ChecklistRepository


class ChecklistService:
    def __init__(self, checklist_repo: ChecklistRepository) -> None:
        self._checklists = checklist_repo

    async def add_checklist_item(
        self,
        *,
        user_id: int,
        user_disaster_id: int,
        title: str | None,
        checklist_date: date | None,
        priority: int,
    ) -> int:
        if title is None or not title.strip() or checklist_date is None:
            raise AppException(
                status_code=400,
                code=400,
                message="title 또는 checklistDate가 누락되었습니다.",
                error_key="MISSING_REQUIRED_FIELD",
            )
        return await self._checklists.add_checklist_item(
            user_id=user_id,
            user_disaster_id=user_disaster_id,
            title=title.strip(),
            checklist_date=checklist_date,
            priority=priority,
        )

    async def patch_checklist_item(
        self,
        *,
        user_id: int,
        user_disaster_id: int,
        checklist_item_id: int,
        title: str | None,
        checklist_date: date | None,
        is_completed: bool | None,
        priority: int | None,
        has_any_field: bool,
    ) -> int:
        if not has_any_field:
            raise AppException(
                status_code=400,
                code=400,
                message="수정할 필드를 하나 이상 전달해야 합니다.",
                error_key="MISSING_REQUIRED_FIELD",
            )
        return await self._checklists.patch_checklist_item(
            user_id=user_id,
            user_disaster_id=user_disaster_id,
            checklist_item_id=checklist_item_id,
            title=title.strip() if isinstance(title, str) else None,
            checklist_date=checklist_date,
            is_completed=is_completed,
            priority=priority,
        )

    async def add_attachment(
        self,
        *,
        user_id: int,
        user_disaster_id: int,
        checklist_item_id: int,
        attachment_type: str | None,
        content: str | None,
        file_url: str | None,
        original_file_name: str | None,
        mime_type: str | None,
        file_size: int | None,
        thumbnail_url: str | None,
    ) -> int:
        normalized_type = self._validate_attachment_type(attachment_type)
        normalized_content = content.strip() if isinstance(content, str) else None
        normalized_file_url = file_url.strip() if isinstance(file_url, str) else None
        normalized_name = original_file_name.strip() if isinstance(original_file_name, str) else None
        self._validate_attachment_payload(
            attachment_type=normalized_type,
            content=normalized_content,
            file_url=normalized_file_url,
            original_file_name=normalized_name,
            file_size=file_size,
        )
        return await self._checklists.add_attachment(
            user_id=user_id,
            user_disaster_id=user_disaster_id,
            checklist_item_id=checklist_item_id,
            attachment_type=normalized_type,
            content=normalized_content,
            file_url=normalized_file_url,
            original_file_name=normalized_name,
            mime_type=mime_type,
            file_size=file_size,
            thumbnail_url=thumbnail_url,
        )

    async def patch_attachment(
        self,
        *,
        user_id: int,
        user_disaster_id: int,
        checklist_item_id: int,
        attachment_id: int,
        content: str | None,
        file_url: str | None,
        original_file_name: str | None,
        mime_type: str | None,
        file_size: int | None,
        thumbnail_url: str | None,
        has_any_field: bool,
    ) -> int:
        if not has_any_field:
            raise AppException(
                status_code=400,
                code=400,
                message="수정할 필드를 하나 이상 전달해야 합니다.",
                error_key="MISSING_REQUIRED_FIELD",
            )
        normalized_content = content.strip() if isinstance(content, str) else None
        normalized_file_url = file_url.strip() if isinstance(file_url, str) else None
        normalized_name = original_file_name.strip() if isinstance(original_file_name, str) else None
        if normalized_file_url is not None:
            self._validate_firebase_storage_url(normalized_file_url)
        if file_size is not None and file_size > 10 * 1024 * 1024:
            raise AppException(
                status_code=400,
                code=400,
                message="파일 용량은 10MB 이하여야 합니다.",
                error_key="FILE_SIZE_EXCEEDED",
            )
        return await self._checklists.patch_attachment(
            user_id=user_id,
            user_disaster_id=user_disaster_id,
            checklist_item_id=checklist_item_id,
            attachment_id=attachment_id,
            content=normalized_content,
            file_url=normalized_file_url,
            original_file_name=normalized_name,
            mime_type=mime_type,
            file_size=file_size,
            thumbnail_url=thumbnail_url,
        )

    async def delete_attachment(
        self,
        *,
        user_id: int,
        user_disaster_id: int,
        checklist_item_id: int,
        attachment_id: int,
    ) -> int:
        return await self._checklists.delete_attachment(
            user_id=user_id,
            user_disaster_id=user_disaster_id,
            checklist_item_id=checklist_item_id,
            attachment_id=attachment_id,
        )

    def _validate_attachment_type(self, attachment_type: str | None) -> str:
        if attachment_type is None or not attachment_type.strip():
            raise AppException(
                status_code=400,
                code=400,
                message="attachmentType이 필요합니다.",
                error_key="MISSING_REQUIRED_FIELD",
            )
        normalized = attachment_type.strip().upper()
        if normalized not in {"MEMO", "IMAGE", "FILE"}:
            raise AppException(
                status_code=400,
                code=400,
                message="attachmentType은 MEMO, IMAGE, FILE만 허용됩니다.",
                error_key="INVALID_ATTACHMENT_TYPE",
            )
        return normalized

    def _validate_attachment_payload(
        self,
        *,
        attachment_type: str,
        content: str | None,
        file_url: str | None,
        original_file_name: str | None,
        file_size: int | None,
    ) -> None:
        if attachment_type == "MEMO":
            if content is None or not content:
                raise AppException(
                    status_code=400,
                    code=400,
                    message="MEMO 타입에는 content가 필요합니다.",
                    error_key="MISSING_MEMO_CONTENT",
                )
            return

        if file_url is None or not file_url:
            raise AppException(
                status_code=400,
                code=400,
                message="fileUrl이 필요합니다.",
                error_key="MISSING_FILE_URL",
            )
        if original_file_name is None or not original_file_name:
            raise AppException(
                status_code=400,
                code=400,
                message="originalFileName이 필요합니다.",
                error_key="MISSING_FILE_NAME",
            )
        self._validate_firebase_storage_url(file_url)
        if file_size is not None and file_size > 10 * 1024 * 1024:
            raise AppException(
                status_code=400,
                code=400,
                message="파일 용량은 10MB 이하여야 합니다.",
                error_key="FILE_SIZE_EXCEEDED",
            )

    def _validate_firebase_storage_url(self, url: str) -> None:
        parsed = urlparse(url)
        if parsed.scheme != "https":
            raise AppException(
                status_code=400,
                code=400,
                message="Firebase Storage URL만 허용됩니다.",
                error_key="INVALID_FILE_URL",
            )
        host = parsed.hostname or ""
        if host not in {"firebasestorage.googleapis.com", "storage.googleapis.com"}:
            raise AppException(
                status_code=400,
                code=400,
                message="Firebase Storage URL만 허용됩니다.",
                error_key="INVALID_FILE_URL",
            )
