from __future__ import annotations

import json
from datetime import date, datetime, timedelta
from urllib.parse import urlparse

from app.common.exceptions import AppException
from app.config import settings
from app.domain.checklist.entity import ChecklistItem
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

    async def patch_checklist_status(
        self,
        *,
        user_id: int,
        user_disaster_id: int,
        checklist_item_id: int,
        is_completed: bool | None,
    ) -> tuple[int, bool, datetime | None]:
        if is_completed is None:
            raise AppException(
                status_code=400,
                code=400,
                message="isCompleted가 필요합니다.",
                error_key="MISSING_REQUIRED_FIELD",
            )
        return await self._checklists.patch_checklist_status(
            user_id=user_id,
            user_disaster_id=user_disaster_id,
            checklist_item_id=checklist_item_id,
            completed=is_completed,
        )

    async def delete_checklist_item(
        self,
        *,
        user_id: int,
        user_disaster_id: int,
        checklist_item_id: int,
    ) -> tuple[int, int]:
        return await self._checklists.delete_checklist_item(
            user_id=user_id,
            user_disaster_id=user_disaster_id,
            checklist_item_id=checklist_item_id,
        )

    async def get_checklist_detail(
        self,
        *,
        user_id: int,
        user_disaster_id: int,
        checklist_item_id: int,
    ) -> tuple[dict[str, object], list[dict[str, object]]]:
        return await self._checklists.get_checklist_detail(
            user_id=user_id,
            user_disaster_id=user_disaster_id,
            checklist_item_id=checklist_item_id,
        )

    async def get_checklists_by_date_range(
        self,
        *,
        user_id: int,
        user_disaster_id: int,
        date_value: date | None,
        start_date: date | None,
        end_date: date | None,
    ) -> tuple[date, date, list[dict[str, object]]]:
        if date_value is not None and (start_date is not None or end_date is not None):
            raise AppException(
                status_code=400,
                code=400,
                message="date와 기간(startDate/endDate)을 동시에 보낼 수 없습니다.",
                error_key="INVALID_DATE_RANGE",
            )
        if date_value is None and (start_date is None or end_date is None):
            raise AppException(
                status_code=400,
                code=400,
                message="date 또는 startDate/endDate를 전달해야 합니다.",
                error_key="MISSING_REQUIRED_FIELD",
            )

        if date_value is not None:
            resolved_start = date_value
            resolved_end = date_value
        else:
            assert start_date is not None and end_date is not None
            if start_date > end_date:
                raise AppException(
                    status_code=400,
                    code=400,
                    message="startDate는 endDate보다 늦을 수 없습니다.",
                    error_key="INVALID_DATE_RANGE",
                )
            if (end_date - start_date).days > 30:
                raise AppException(
                    status_code=400,
                    code=400,
                    message="조회 범위는 최대 31일입니다.",
                    error_key="INVALID_DATE_RANGE",
                )
            resolved_start = start_date
            resolved_end = end_date

        rows = await self._checklists.get_checklists_by_date_range(
            user_id=user_id,
            user_disaster_id=user_disaster_id,
            start_date=resolved_start,
            end_date=resolved_end,
        )
        return resolved_start, resolved_end, rows

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
        normalized_type = archive_type.upper()
        if normalized_type not in {"ALL", "MEMO", "IMAGE", "FILE"}:
            raise AppException(
                status_code=400,
                code=400,
                message="type은 ALL, MEMO, IMAGE, FILE만 허용됩니다.",
                error_key="INVALID_ATTACHMENT_TYPE",
            )
        if limit < 1 or limit > 50:
            raise AppException(
                status_code=400,
                code=400,
                message="limit은 1~50 사이여야 합니다.",
                error_key="INVALID_LIMIT",
            )
        return await self._checklists.get_archives(
            user_id=user_id,
            user_disaster_id=user_disaster_id,
            archive_type=normalized_type,
            date_value=date_value,
            cursor=cursor,
            limit=limit,
        )

    async def update_context(
        self,
        *,
        user_id: int,
        user_disaster_id: int,
        can_go_out: bool,
        available_time: str,
        special_notes: str | None = None,
    ) -> None:
        normalized_time = available_time.strip().upper()
        if normalized_time not in {"UNDER_ONE_HOUR", "ONE_TO_THREE_HOURS", "ALL_DAY_HALF_DAY"}:
            raise AppException(
                status_code=400,
                code=400,
                message="availableTime 값이 유효하지 않습니다.",
                error_key="INVALID_AVAILABLE_TIME",
            )
        normalized_notes = special_notes.strip() if isinstance(special_notes, str) else None
        await self._checklists.update_context(
            user_id=user_id,
            user_disaster_id=user_disaster_id,
            can_go_out=can_go_out,
            available_time=normalized_time,
            special_notes=normalized_notes,
        )

    async def generate_ai_checklist(
        self,
        *,
        user_id: int,
        user_disaster_id: int,
        target_date: date,
    ) -> list[ChecklistItem]:
        impact_full = await self._checklists.get_impact_full(
            user_id=user_id,
            user_disaster_id=user_disaster_id,
        )
        if impact_full is None:
            raise AppException(
                status_code=404,
                code=404,
                message="해당 사용자의 재난 온보딩 정보가 존재하지 않습니다.",
                error_key="DISASTER_IMPACT_NOT_FOUND",
            )

        special_notes = str(impact_full.get("special_notes") or "")
        prompt = self._build_ai_prompt(impact_full, special_notes=special_notes or None)
        titles = self._call_gemini(prompt)

        items = [
            ChecklistItem(
                user_disaster_id=user_disaster_id,
                checklist_date=target_date,
                title=title.strip(),
                item_source_type="AI_GENERATED",
                priority=1,
            )
            for title in titles[:3]
        ]
        return await self._checklists.save_items(items)

    async def get_weekly_completion_stats(
        self,
        *,
        user_id: int,
        target_date: date,
    ) -> tuple[date, date, int, int, float]:
        user_disaster_id = await self._checklists.get_active_user_disaster_id(user_id)
        if user_disaster_id is None:
            raise AppException(
                status_code=404,
                code=404,
                message="활성화된 재난 정보가 없습니다.",
                error_key="DISASTER_NOT_FOUND",
            )
        # 프론트에서 전달한 기준일(target_date)을 포함한 최근 7일 범위
        week_end = target_date
        week_start = target_date - timedelta(days=6)
        total_tasks, completed_tasks = await self._checklists.get_weekly_completion_stats(
            user_disaster_id=user_disaster_id,
            week_start_date=week_start,
            week_end_date=week_end,
        )
        completion_rate = 0.0 if total_tasks == 0 else round((completed_tasks / total_tasks) * 100, 1)
        return week_start, week_end, total_tasks, completed_tasks, completion_rate

    def _build_ai_prompt(self, impact_full: dict[str, object], *, special_notes: str | None = None) -> str:
        disaster_type = str(impact_full.get("disaster_type", "")).upper()
        safety_status = str(impact_full.get("safety_status") or "")
        residence_status = str(impact_full.get("residence_status") or "")
        can_go_out = bool(impact_full.get("can_go_out"))
        available_time = str(impact_full.get("available_time") or "")
        detail = impact_full.get("detail")
        detail_text = json.dumps(detail, ensure_ascii=False) if detail is not None else "없음"

        can_go_out_str = "가능(TRUE)" if can_go_out else "불가능(FALSE)"
        time_map = {
            "UNDER_ONE_HOUR": "1시간 이내",
            "ONE_TO_THREE_HOURS": "1~3시간",
            "ALL_DAY_HALF_DAY": "반나절~하루",
        }
        avail_time_str = time_map.get(available_time, "알 수 없음")

        notes_line = f"\n- 특이 사항: {special_notes}" if special_notes else ""

        return f"""사용자는 재난 이후 회복 과정에 있습니다. 다음 정보를 바탕으로 오늘 수행할 맞춤형 체크리스트를 생성해주세요.

[재난 상황]
- 재난 유형: {disaster_type}
- 상세 정보: {detail_text}
- 안전 상태: {safety_status}
- 거주 상태: {residence_status}

[사용자 상태]
- 외출 가능 여부: {can_go_out_str}
- 외출 가능 시간: {avail_time_str}{notes_line}

조건:
1. 반드시 딱 3개의 할 일(title)만 생성할 것
2. 현실적으로 수행 가능해야 함
3. 구체적인 행동 단위
4. 특이 사항이 있으면 반드시 반영할 것

반드시 아래 JSON 형식으로만 반환하세요:
[
  {{"title": "..."}},
  {{"title": "..."}},
  {{"title": "..."}}
]"""

    def _call_gemini(self, prompt: str) -> list[str]:
        api_key = settings.GEMINI_API_KEY
        if not api_key:
            return ["가족 지인에게 안전 연락하기", "파손된 물건 사진 찍어두기", "식수 및 비상식량 확인하기"]

        try:
            import google.generativeai as genai

            genai.configure(api_key=api_key)
            model = genai.GenerativeModel(
                "gemini-3.5-flash",
                generation_config={"response_mime_type": "application/json"},
            )
            response = model.generate_content(prompt)
            print(f"[Gemini OK] tokens_used={getattr(response.usage_metadata, 'total_token_count', 'N/A')}")
            payload = json.loads(response.text)
            titles = [str(item.get("title", "")).strip() for item in payload if isinstance(item, dict)]
            titles = [t for t in titles if t]
            if len(titles) > 3:
                titles = titles[:3]
            elif len(titles) < 3:
                titles += ["안전 상태 다시 한번 확인하기"] * (3 - len(titles))
            return titles
        except Exception as e:
            print(f"[Gemini Error] {type(e).__name__}: {e}")
            return ["가족 지인에게 안전 연락하기", "파손된 물건 사진 찍어두기", "식수 및 비상식량 확인하기"]

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
