from __future__ import annotations

import base64
import json
from datetime import date, datetime

from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.common.exceptions import AppException
from app.domain.checklist.entity import ChecklistItem
from app.domain.checklist.repository import ChecklistRepository
from app.infrastructure.models.checklist_model import ArchiveFileModel, ArchiveItemModel, ChecklistItemModel
from app.infrastructure.models.disaster_model import (
    DisasterImpactModel,
    RegistrationStatus,
    UserDisasterModel,
)
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

    async def patch_checklist_status(
        self,
        *,
        user_id: int,
        user_disaster_id: int,
        checklist_item_id: int,
        completed: bool,
    ) -> tuple[int, bool, datetime | None]:
        await self._assert_active_disaster(user_id=user_id, user_disaster_id=user_disaster_id)
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
        item.is_completed = completed
        item.completed_at = datetime.utcnow() if completed else None
        await self._session.flush()
        return int(item.checklist_item_id), item.is_completed, item.completed_at

    async def delete_checklist_item(
        self,
        *,
        user_id: int,
        user_disaster_id: int,
        checklist_item_id: int,
    ) -> tuple[int, int]:
        await self._assert_active_disaster(user_id=user_id, user_disaster_id=user_disaster_id)
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
        attachment_count_result = await self._session.execute(
            select(func.count(ArchiveItemModel.archive_item_id)).where(
                ArchiveItemModel.checklist_item_id == checklist_item_id
            )
        )
        attachment_count = int(attachment_count_result.scalar_one() or 0)
        await self._session.delete(item)
        await self._session.flush()
        return int(checklist_item_id), attachment_count

    async def get_checklist_detail(
        self,
        *,
        user_id: int,
        user_disaster_id: int,
        checklist_item_id: int,
    ) -> tuple[dict[str, object], list[dict[str, object]]]:
        await self._assert_active_disaster(user_id=user_id, user_disaster_id=user_disaster_id)
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
        attachment_result = await self._session.execute(
            select(ArchiveItemModel, ArchiveFileModel).outerjoin(
                ArchiveFileModel,
                ArchiveFileModel.archive_item_id == ArchiveItemModel.archive_item_id,
            ).where(
                ArchiveItemModel.checklist_item_id == checklist_item_id
            ).order_by(ArchiveItemModel.created_at.asc())
        )
        attachments: list[dict[str, object]] = []
        for archive_item, archive_file in attachment_result.all():
            attachment_type = (archive_item.archive_type or "").upper()
            attachments.append(
                {
                    "attachmentId": int(archive_item.archive_item_id),
                    "attachmentType": attachment_type,
                    "content": archive_item.description,
                    "fileUrl": archive_file.file_url if archive_file else None,
                    "originalFileName": archive_file.original_file_name if archive_file else None,
                    "mimeType": archive_file.mime_type if archive_file else None,
                    "fileSize": int(archive_file.file_size) if archive_file and archive_file.file_size is not None else None,
                    "thumbnailUrl": archive_file.thumbnail_url if archive_file else None,
                    "createdAt": archive_item.created_at,
                }
            )
        return (
            {
                "checklistId": int(item.checklist_item_id),
                "title": item.title,
                "isCompleted": item.is_completed,
                "completedAt": item.completed_at,
                "checklistDate": item.checklist_date.isoformat(),
                "priority": int(item.priority),
                "isAiGenerated": item.item_source_type == "AI_GENERATED",
            },
            attachments,
        )

    async def get_checklists_by_date_range(
        self,
        *,
        user_id: int,
        user_disaster_id: int,
        start_date: date,
        end_date: date,
    ) -> list[dict[str, object]]:
        await self._assert_active_disaster(user_id=user_id, user_disaster_id=user_disaster_id)
        rows = await self._get_owned_checklists_by_range(
            user_disaster_id=user_disaster_id,
            start_date=start_date,
            end_date=end_date,
        )
        if not rows:
            return []
        checklist_ids = [int(row.checklist_item_id) for row in rows]
        summary_result = await self._session.execute(
            select(
                ArchiveItemModel.checklist_item_id,
                func.sum(
                    case((ArchiveItemModel.archive_type == "MEMO", 1), else_=0)
                ).label("memo_count"),
                func.sum(
                    case((ArchiveItemModel.archive_type == "IMAGE", 1), else_=0)
                ).label("image_count"),
                func.sum(
                    case((ArchiveItemModel.archive_type == "FILE", 1), else_=0)
                ).label("file_count"),
            ).where(
                ArchiveItemModel.checklist_item_id.in_(checklist_ids)
            ).group_by(ArchiveItemModel.checklist_item_id)
        )
        summary_map = {
            int(checklist_item_id): (
                int(memo_count or 0),
                int(image_count or 0),
                int(file_count or 0),
            )
            for checklist_item_id, memo_count, image_count, file_count in summary_result.all()
        }
        return [
            {
                "checklistItemId": int(row.checklist_item_id),
                "checklistDate": row.checklist_date.isoformat(),
                "title": row.title,
                "isCompleted": row.is_completed,
                "priority": int(row.priority),
                "isAiGenerated": row.item_source_type == "AI_GENERATED",
                "attachmentSummary": {
                    "MEMO": summary_map.get(int(row.checklist_item_id), (0, 0, 0))[0],
                    "IMAGE": summary_map.get(int(row.checklist_item_id), (0, 0, 0))[1],
                    "FILE": summary_map.get(int(row.checklist_item_id), (0, 0, 0))[2],
                },
            }
            for row in rows
        ]

    async def get_archives(
        self,
        *,
        user_id: int,
        user_disaster_id: int,
        archive_type: str,
        date_value: date | None,
        cursor: str | None,
        limit: int,
    ) -> tuple[list[dict[str, object]], str | None, bool]:
        await self._assert_active_disaster(user_id=user_id, user_disaster_id=user_disaster_id)
        cursor_id: int | None = None
        if cursor is not None:
            try:
                decoded = base64.b64decode(cursor).decode("utf-8")
                payload = json.loads(decoded)
                cursor_id = int(payload["id"])
            except Exception as exc:
                raise AppException(
                    status_code=400,
                    code=400,
                    message="cursor 형식이 유효하지 않습니다.",
                    error_key="INVALID_CURSOR",
                ) from exc

        stmt = (
            select(
                ArchiveItemModel,
                ArchiveFileModel,
                ChecklistItemModel.title,
                ChecklistItemModel.checklist_date,
            )
            .join(
                ChecklistItemModel,
                ChecklistItemModel.checklist_item_id == ArchiveItemModel.checklist_item_id,
            )
            .outerjoin(
                ArchiveFileModel,
                ArchiveFileModel.archive_item_id == ArchiveItemModel.archive_item_id,
            )
            .where(ChecklistItemModel.user_disaster_id == user_disaster_id)
            .order_by(ArchiveItemModel.archive_item_id.desc())
            .limit(limit + 1)
        )
        if archive_type != "ALL":
            stmt = stmt.where(ArchiveItemModel.archive_type == archive_type)
        if date_value is not None:
            stmt = stmt.where(ChecklistItemModel.checklist_date == date_value)
        if cursor_id is not None:
            stmt = stmt.where(ArchiveItemModel.archive_item_id < cursor_id)

        result = await self._session.execute(stmt)
        rows = result.all()
        has_more = len(rows) > limit
        rows = rows[:limit]

        items = [
            {
                "attachmentId": int(archive_item.archive_item_id),
                "checklistItemId": int(archive_item.checklist_item_id),
                "checklistItemTitle": checklist_title or "",
                "attachmentType": archive_item.archive_type,
                "fileUrl": archive_file.file_url if archive_file else None,
                "originalFileName": archive_file.original_file_name if archive_file else None,
                "mimeType": archive_file.mime_type if archive_file else None,
                "thumbnailUrl": archive_file.thumbnail_url if archive_file else None,
                "checklistDate": checklist_date.isoformat(),
                "createdAt": archive_item.created_at,
            }
            for archive_item, archive_file, checklist_title, checklist_date in rows
        ]
        next_cursor = None
        if has_more and rows:
            next_cursor = base64.b64encode(
                json.dumps({"id": int(rows[-1][0].archive_item_id)}).encode("utf-8")
            ).decode("utf-8")
        return items, next_cursor, has_more

    async def save_items(self, items: list[ChecklistItem]) -> list[ChecklistItem]:
        models = [
            ChecklistItemModel(
                user_disaster_id=item.user_disaster_id,
                checklist_date=item.checklist_date,
                title=item.title,
                memo=item.memo,
                item_source_type=item.item_source_type,
                priority=item.priority,
                is_completed=item.is_completed,
                completed_at=item.completed_at,
            )
            for item in items
        ]
        self._session.add_all(models)
        await self._session.flush()
        for model in models:
            await self._session.refresh(model)
        return [
            ChecklistItem(
                checklist_item_id=int(model.checklist_item_id),
                user_disaster_id=int(model.user_disaster_id),
                checklist_date=model.checklist_date,
                title=model.title,
                memo=model.memo,
                item_source_type=model.item_source_type,
                priority=int(model.priority),
                is_completed=bool(model.is_completed),
                completed_at=model.completed_at,
            )
            for model in models
        ]

    async def get_impact_full(
        self,
        *,
        user_id: int,
        user_disaster_id: int,
    ) -> dict[str, object] | None:
        row = await self._get_owned_disaster(user_id=user_id, user_disaster_id=user_disaster_id)
        if row is None:
            raise AppException(
                status_code=404,
                code=404,
                message="존재하지 않는 재난입니다.",
                error_key="DISASTER_NOT_FOUND",
            )
        result = await self._session.execute(
            select(DisasterImpactModel)
            .where(DisasterImpactModel.user_disaster_id == user_disaster_id)
            .options(
                selectinload(DisasterImpactModel.flood_detail),
                selectinload(DisasterImpactModel.earthquake_detail),
                selectinload(DisasterImpactModel.typhoon_detail),
                selectinload(DisasterImpactModel.fire_detail),
            )
        )
        impact = result.scalar_one_or_none()
        if impact is None:
            return None
        detail: dict[str, object] | None = None
        if row.disaster_type and row.disaster_type.disaster_code == "FLOOD" and impact.flood_detail:
            d = impact.flood_detail
            detail = {
                "floodLevel": d.flood_level.value,
                "waterDrainStatus": d.water_drain_status.value,
                "damageHouse": d.damage_house,
                "damageVehicle": d.damage_vehicle,
                "electricProblem": d.electric_problem,
                "waterProblem": d.water_problem,
            }
        elif row.disaster_type and row.disaster_type.disaster_code == "EARTHQUAKE" and impact.earthquake_detail:
            d = impact.earthquake_detail
            detail = {
                "aftershockFeeling": d.aftershock_feeling.value,
                "buildingCrack": d.building_crack,
                "houseDamage": d.house_damage,
                "vehicleDamage": d.vehicle_damage,
                "electricProblem": d.electric_problem,
                "waterProblem": d.water_problem,
            }
        elif row.disaster_type and row.disaster_type.disaster_code == "TYPHOON" and impact.typhoon_detail:
            d = impact.typhoon_detail
            detail = {
                "roofDamage": d.roof_damage,
                "windowDamage": d.window_damage,
                "structureDamage": d.structure_damage,
                "vehicleDamage": d.vehicle_damage,
                "electricProblem": d.electric_problem,
                "waterProblem": d.water_problem,
            }
        elif row.disaster_type and row.disaster_type.disaster_code == "FIRE" and impact.fire_detail:
            d = impact.fire_detail
            detail = {
                "fireDamageScope": d.fire_damage_scope.value,
                "smokeInhalation": d.smoke_inhalation.value,
                "houseDamage": d.house_damage,
                "sootDamage": d.soot_damage,
                "debrisExist": d.debris_exist,
                "vehicleDamage": d.vehicle_damage,
                "electricProblem": d.electric_problem,
                "waterProblem": d.water_problem,
            }
        return {
            "disaster_type": row.disaster_type.disaster_code if row.disaster_type else "",
            "safety_status": impact.safety_status.value if impact.safety_status else None,
            "residence_status": impact.residence_status.value if impact.residence_status else None,
            "can_go_out": impact.can_go_out,
            "available_time": impact.available_time.value if impact.available_time else None,
            "detail": detail,
        }

    async def update_context(
        self,
        *,
        user_id: int,
        user_disaster_id: int,
        can_go_out: bool,
        available_time: str,
    ) -> None:
        row = await self._assert_active_disaster(user_id=user_id, user_disaster_id=user_disaster_id)
        result = await self._session.execute(
            select(DisasterImpactModel).where(DisasterImpactModel.user_disaster_id == row.user_disaster_id)
        )
        impact = result.scalar_one_or_none()
        if impact is None:
            raise AppException(
                status_code=404,
                code=404,
                message="해당 userDisasterId에 대한 온보딩 정보를 찾을 수 없습니다.",
                error_key="DISASTER_IMPACT_NOT_FOUND",
            )
        impact.can_go_out = can_go_out
        impact.available_time = available_time
        await self._session.flush()

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

    async def _get_owned_checklists_by_range(
        self,
        *,
        user_disaster_id: int,
        start_date: date,
        end_date: date,
    ) -> list[ChecklistItemModel]:
        result = await self._session.execute(
            select(ChecklistItemModel).where(
                ChecklistItemModel.user_disaster_id == user_disaster_id,
                ChecklistItemModel.checklist_date >= start_date,
                ChecklistItemModel.checklist_date <= end_date,
            ).order_by(
                ChecklistItemModel.checklist_date.asc(),
                ChecklistItemModel.priority.asc(),
                ChecklistItemModel.checklist_item_id.asc(),
            )
        )
        return result.scalars().all()

    async def _assert_active_disaster(
        self,
        *,
        user_id: int,
        user_disaster_id: int,
    ) -> UserDisasterModel:
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
        return row

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
