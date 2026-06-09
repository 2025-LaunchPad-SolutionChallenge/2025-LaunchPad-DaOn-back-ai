from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.exceptions import AppException
from app.domain.checklist.repository import ChecklistRepository
from app.infrastructure.models.checklist_model import ArchiveFileModel, ArchiveItemModel, ChecklistItemModel
from app.infrastructure.models.disaster_model import RegistrationStatus, UserDisasterModel
from app.infrastructure.models.user_model import UserSettingModel


class SqlAlchemyChecklistRepository(ChecklistRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add_checklist_item(
        self,
        *,
        user_id: int,
        user_disaster_id: int,
        title: str,
        checklist_date: date,
        priority: int,
    ) -> int:
        row = await self._get_owned_disaster(user_id=user_id, user_disaster_id=user_disaster_id)
        if row is None:
            raise AppException(
                status_code=404,
                code=404,
                message="존재하지 않는 재난입니다.",
                error_key="DISASTER_NOT_FOUND",
            )
        if row.registration_status != RegistrationStatus.ACTIVE:
            raise AppException(
                status_code=409,
                code=409,
                message="ACTIVE 상태 재난만 수정할 수 있습니다.",
                error_key="DISASTER_NOT_ACTIVE",
            )
        item = ChecklistItemModel(
            user_disaster_id=user_disaster_id,
            checklist_date=checklist_date,
            title=title,
            item_source_type="MANUAL",
            priority=priority,
            is_completed=False,
            completed_at=None,
        )
        self._session.add(item)
        await self._session.flush()
        return int(item.checklist_item_id)

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
    ) -> int:
        row = await self._get_owned_disaster(user_id=user_id, user_disaster_id=user_disaster_id)
        if row is None:
            raise AppException(
                status_code=404,
                code=404,
                message="존재하지 않는 재난입니다.",
                error_key="DISASTER_NOT_FOUND",
            )
        if row.registration_status != RegistrationStatus.ACTIVE:
            raise AppException(
                status_code=409,
                code=409,
                message="ACTIVE 상태 재난만 수정할 수 있습니다.",
                error_key="DISASTER_NOT_ACTIVE",
            )
        item = await self._get_checklist_item(
            checklist_item_id=checklist_item_id,
            user_disaster_id=user_disaster_id,
        )
        if item is None:
            raise AppException(
                status_code=404,
                code=404,
                message="체크리스트 항목을 찾을 수 없습니다.",
                error_key="CHECKLIST_ITEM_NOT_FOUND",
            )
        if title is not None:
            item.title = title
        if checklist_date is not None:
            item.checklist_date = checklist_date
        if priority is not None:
            item.priority = priority
        if is_completed is not None:
            item.is_completed = is_completed
            item.completed_at = datetime.utcnow() if is_completed else None
        await self._session.flush()
        return int(item.checklist_item_id)

    async def add_attachment(
        self,
        *,
        user_id: int,
        user_disaster_id: int,
        checklist_item_id: int,
        attachment_type: str,
        content: str | None,
        file_url: str | None,
        original_file_name: str | None,
        mime_type: str | None,
        file_size: int | None,
        thumbnail_url: str | None,
    ) -> int:
        await self._assert_active_disaster_and_item(
            user_id=user_id,
            user_disaster_id=user_disaster_id,
            checklist_item_id=checklist_item_id,
        )

        user_setting = await self._get_or_create_user_setting(
            user_id=user_id,
            user_disaster_id=user_disaster_id,
        )
        archive_item = ArchiveItemModel(
            user_setting_id=user_setting.user_setting_id,
            checklist_item_id=checklist_item_id,
            archive_date=date.today(),
            archive_type=attachment_type,
            title=original_file_name,
            description=content,
        )
        self._session.add(archive_item)
        await self._session.flush()
        if attachment_type in {"IMAGE", "FILE"}:
            archive_file = ArchiveFileModel(
                archive_item_id=archive_item.archive_item_id,
                original_file_name=original_file_name or "file",
                stored_file_name=original_file_name or "file",
                file_url=file_url or "",
                mime_type=mime_type,
                file_size=file_size,
                thumbnail_url=thumbnail_url,
            )
            self._session.add(archive_file)
            await self._session.flush()
        return int(archive_item.archive_item_id)

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
    ) -> int:
        await self._assert_active_disaster_and_item(
            user_id=user_id,
            user_disaster_id=user_disaster_id,
            checklist_item_id=checklist_item_id,
        )
        attachment = await self._get_attachment(
            attachment_id=attachment_id,
            checklist_item_id=checklist_item_id,
        )
        if attachment is None:
            raise AppException(
                status_code=404,
                code=404,
                message="첨부를 찾을 수 없습니다.",
                error_key="ATTACHMENT_NOT_FOUND",
            )
        attachment_type = (attachment.archive_type or "").upper()
        archive_file = await self._get_archive_file(attachment.archive_item_id)

        if attachment_type == "MEMO":
            if file_url is not None or original_file_name is not None:
                raise AppException(
                    status_code=400,
                    code=400,
                    message="MEMO 타입 첨부에 파일 필드는 허용되지 않습니다.",
                    error_key="ATTACHMENT_TYPE_MISMATCH",
                )
            if content is not None and not content:
                raise AppException(
                    status_code=400,
                    code=400,
                    message="MEMO 타입에는 content가 필요합니다.",
                    error_key="MISSING_MEMO_CONTENT",
                )
            if content is not None:
                attachment.description = content
            await self._session.flush()
            return int(attachment.archive_item_id)

        if content is not None:
            raise AppException(
                status_code=400,
                code=400,
                message="파일 타입 첨부에 content는 허용되지 않습니다.",
                error_key="ATTACHMENT_TYPE_MISMATCH",
            )
        if file_url is not None and not file_url:
            raise AppException(
                status_code=400,
                code=400,
                message="fileUrl이 필요합니다.",
                error_key="MISSING_FILE_URL",
            )
        if archive_file is None:
            raise AppException(
                status_code=404,
                code=404,
                message="첨부 파일을 찾을 수 없습니다.",
                error_key="ATTACHMENT_NOT_FOUND",
            )
        if file_url is not None:
            archive_file.file_url = file_url
        if original_file_name is not None:
            archive_file.original_file_name = original_file_name
            archive_file.stored_file_name = original_file_name
            attachment.title = original_file_name
        if mime_type is not None:
            archive_file.mime_type = mime_type
        if file_size is not None:
            archive_file.file_size = file_size
        if thumbnail_url is not None:
            archive_file.thumbnail_url = thumbnail_url
        await self._session.flush()
        return int(attachment.archive_item_id)

    async def delete_attachment(
        self,
        *,
        user_id: int,
        user_disaster_id: int,
        checklist_item_id: int,
        attachment_id: int,
    ) -> int:
        await self._assert_active_disaster_and_item(
            user_id=user_id,
            user_disaster_id=user_disaster_id,
            checklist_item_id=checklist_item_id,
        )
        attachment = await self._get_attachment(
            attachment_id=attachment_id,
            checklist_item_id=checklist_item_id,
        )
        if attachment is None:
            raise AppException(
                status_code=404,
                code=404,
                message="첨부를 찾을 수 없습니다.",
                error_key="ATTACHMENT_NOT_FOUND",
            )
        await self._session.delete(attachment)
        await self._session.flush()
        return int(attachment_id)

    async def _get_owned_disaster(
        self,
        *,
        user_id: int,
        user_disaster_id: int,
    ) -> UserDisasterModel | None:
        result = await self._session.execute(
            select(UserDisasterModel).where(UserDisasterModel.user_disaster_id == user_disaster_id)
        )
        row = result.scalar_one_or_none()
        if row is None:
            return None
        if row.user_id != user_id:
            raise AppException(
                status_code=403,
                code=403,
                message="본인 재난만 접근할 수 있습니다.",
                error_key="FORBIDDEN",
            )
        return row

    async def _get_checklist_item(
        self,
        *,
        checklist_item_id: int,
        user_disaster_id: int,
    ) -> ChecklistItemModel | None:
        result = await self._session.execute(
            select(ChecklistItemModel).where(
                ChecklistItemModel.checklist_item_id == checklist_item_id,
                ChecklistItemModel.user_disaster_id == user_disaster_id,
            )
        )
        return result.scalar_one_or_none()

    async def _get_or_create_user_setting(
        self,
        *,
        user_id: int,
        user_disaster_id: int,
    ) -> UserSettingModel:
        result = await self._session.execute(
            select(UserSettingModel).where(UserSettingModel.user_id == user_id)
        )
        row = result.scalar_one_or_none()
        if row is not None:
            if row.user_disaster_id != user_disaster_id:
                row.user_disaster_id = user_disaster_id
            return row
        row = UserSettingModel(
            user_id=user_id,
            allow_push_notification=None,
            user_disaster_id=user_disaster_id,
        )
        self._session.add(row)
        await self._session.flush()
        return row

    async def _get_attachment(
        self,
        *,
        attachment_id: int,
        checklist_item_id: int,
    ) -> ArchiveItemModel | None:
        result = await self._session.execute(
            select(ArchiveItemModel).where(
                ArchiveItemModel.archive_item_id == attachment_id,
                ArchiveItemModel.checklist_item_id == checklist_item_id,
            )
        )
        return result.scalar_one_or_none()

    async def _get_archive_file(self, archive_item_id: int) -> ArchiveFileModel | None:
        result = await self._session.execute(
            select(ArchiveFileModel).where(ArchiveFileModel.archive_item_id == archive_item_id)
        )
        return result.scalar_one_or_none()

    async def _assert_active_disaster_and_item(
        self,
        *,
        user_id: int,
        user_disaster_id: int,
        checklist_item_id: int,
    ) -> None:
        row = await self._get_owned_disaster(user_id=user_id, user_disaster_id=user_disaster_id)
        if row is None:
            raise AppException(
                status_code=404,
                code=404,
                message="존재하지 않는 재난입니다.",
                error_key="DISASTER_NOT_FOUND",
            )
        if row.registration_status != RegistrationStatus.ACTIVE:
            raise AppException(
                status_code=409,
                code=409,
                message="ACTIVE 상태 재난만 수정할 수 있습니다.",
                error_key="DISASTER_NOT_ACTIVE",
            )
        item = await self._get_checklist_item(
            checklist_item_id=checklist_item_id,
            user_disaster_id=user_disaster_id,
        )
        if item is None:
            raise AppException(
                status_code=404,
                code=404,
                message="체크리스트 항목을 찾을 수 없습니다.",
                error_key="CHECKLIST_ITEM_NOT_FOUND",
            )
