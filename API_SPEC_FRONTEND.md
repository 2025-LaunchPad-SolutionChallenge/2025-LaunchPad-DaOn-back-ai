# DaOn Backend API Spec (Frontend)

현재 백엔드 코드 기준의 실제 구현 명세입니다.

- 기준 버전: `app/main.py`, `app/interface/*/router.py`, `app/interface/*/schema.py`
- Base URL 예시: `http://localhost:8000`
- API Prefix: `/api/v1`
- 인증 방식: `Authorization: Bearer {accessToken}`
- 문서 URL: `/docs` (Swagger), `/redoc`

---

## 1) 공통 규칙

### 1.1 인증

- 인증이 필요한 API는 Bearer 토큰 필수입니다.
- 토큰 없음/만료/위조 시 `401`.

예시:

```http
Authorization: Bearer eyJhbGci...
```

### 1.2 공통 에러 응답 형태

백엔드 커스텀 예외(`AppException`)는 아래 형식으로 내려갑니다.

```json
{
  "code": "ERROR_KEY_OR_STATUS",
  "message": "에러 메시지",
  "data": null
}
```

자주 사용되는 에러 키:

- `UNAUTHORIZED`
- `FORBIDDEN`
- `DISASTER_NOT_FOUND`
- `DISASTER_NOT_ACTIVE`
- `CHECKLIST_ITEM_NOT_FOUND`
- `MISSING_REQUIRED_FIELD`
- `INVALID_DATE_FORMAT`
- `INVALID_DATE_RANGE`
- `INVALID_FIELD_TYPE`
- `INVALID_ATTACHMENT_TYPE`
- `INVALID_LIMIT`
- `INVALID_CURSOR`

---

## 2) Health

## `GET /health`

서버 상태 체크

응답:

```json
{
  "status": "ok",
  "app": "DaOn"
}
```

---

## 3) Auth API

Prefix: `/api/v1/auth`

## `POST /auth/register`

회원가입(이미 가입된 Firebase 계정이면 로그인처럼 토큰 발급)

요청:

```json
{
  "firebaseToken": "eyJhbGci...",
  "name": "홍길동",
  "birthDate": "1995-03-15"
}
```

응답:

```json
{
  "user": {
    "id": 1,
    "nickname": "홍길동",
    "profileImage": null
  },
  "accessToken": "eyJhbGci...",
  "refreshToken": "eyJhbGci...",
  "isNewUser": true
}
```

## `POST /auth/login`

요청:

```json
{
  "firebaseToken": "eyJhbGci..."
}
```

응답: `register`와 동일 구조

## `POST /auth/refresh`

요청:

```json
{
  "refreshToken": "eyJhbGci..."
}
```

응답:

```json
{
  "accessToken": "eyJhbGci...",
  "refreshToken": "eyJhbGci..."
}
```

## `POST /auth/logout`

인증 필요 + body의 `refreshToken` 필요

응답:

```json
{
  "message": "로그아웃되었습니다."
}
```

## `DELETE /auth/withdraw`

인증 필요

응답:

```json
{
  "message": "계정이 삭제되었습니다."
}
```

## `POST /auth/residence/verify`

거주지 최초 인증. 재난 기준점 + 현재 위치를 받아 거리 검증합니다.

요청:

```json
{
  "disasterLatitude": 37.5665,
  "disasterLongitude": 126.978,
  "currentLatitude": 37.57,
  "currentLongitude": 126.982,
  "currentAddress": "서울특별시 중구 ..."
}
```

응답(성공):

```json
{
  "status": "VERIFIED",
  "verified": true,
  "distanceKm": 0.52,
  "thresholdKm": 10.0,
  "verificationCount": 1,
  "verifiedAt": "2026-02-24T09:41:00Z",
  "expiresAt": "2026-03-26T09:41:00Z",
  "message": "거주지 인증이 완료되었습니다."
}
```

응답(거리 초과):

```json
{
  "status": "NONE",
  "verified": false,
  "distanceKm": 14.3,
  "thresholdKm": 10.0,
  "message": "재난 발생 위치로부터 10km를 벗어나 인증할 수 없습니다."
}
```

주의:

- 기준점은 최초 1회만 저장됩니다. 이후에는 요청의 `disasterLatitude/Longitude`를 보내도 저장된 기준점을 사용합니다.
- 인증 유효기간은 `RESIDENCE_VERIFY_TTL_DAYS`(기본 30일), 임계 반경은 `RESIDENCE_VERIFY_RADIUS_KM`(기본 10km)입니다.
- 쿨다운(`RESIDENCE_VERIFY_COOLDOWN_MIN`, 기본 5분) 내 재시도 시 `429 VERIFY_COOLDOWN` + `Retry-After` 헤더가 내려옵니다.

## `POST /auth/residence/reverify`

거주지 재인증. 현재 위치만 보내면 저장된 기준점과 거리 재검증합니다.

요청:

```json
{
  "currentLatitude": 37.5705,
  "currentLongitude": 126.9815,
  "currentAddress": "서울특별시 중구 ..."
}
```

응답(성공):

```json
{
  "status": "VERIFIED",
  "verified": true,
  "distanceKm": 0.48,
  "thresholdKm": 10.0,
  "verificationCount": 3,
  "verifiedAt": "2026-03-20T11:00:00Z",
  "expiresAt": "2026-04-19T11:00:00Z",
  "message": "거주지 재인증이 완료되었습니다."
}
```

에러:

- `409 BASELINE_NOT_FOUND`: 최초 인증 전 재인증 시도
- `429 VERIFY_COOLDOWN`: 쿨다운 내 재시도

## `GET /auth/residence`

거주지 인증 상태 조회

응답(유효):

```json
{
  "status": "VERIFIED",
  "verified": true,
  "distanceKm": 0.48,
  "thresholdKm": 10.0,
  "verificationCount": 3,
  "verifiedAt": "2026-03-20T11:00:00Z",
  "expiresAt": "2026-04-19T11:00:00Z",
  "daysUntilExpiry": 30
}
```

응답(만료):

```json
{
  "status": "EXPIRED",
  "verified": false,
  "distanceKm": 0.48,
  "thresholdKm": 10.0,
  "verificationCount": 3,
  "verifiedAt": "2026-02-24T09:41:00Z",
  "expiresAt": "2026-03-26T09:41:00Z",
  "daysUntilExpiry": 0,
  "message": "거주지 인증이 만료되었습니다. 재인증이 필요합니다."
}
```

응답(이력 없음):

```json
{
  "status": "NONE",
  "verified": false,
  "message": "거주지 인증 내역이 없습니다."
}
```

---

## 4) Users API

Prefix: `/api/v1/users`

## `GET /users/me`

내 프로필 조회

응답:

```json
{
  "userId": 1,
  "name": "홍길동",
  "nickname": "길동",
  "birthDate": "1995-03-15",
  "age": 30,
  "profileImage": "https://firebasestorage.googleapis.com/...",
  "residenceVerified": false,
  "addressName": "서울특별시 강남구"
}
```

## `PUT /users/me`

`multipart/form-data`로 프로필 일부 수정

필드(모두 optional):

- `nickname`
- `addressName`
- `householdType` (`SINGLE | MULTI`)
- `profileImageUrl`

응답:

```json
{
  "message": "프로필이 수정되었습니다"
}
```

## `POST /users/me/profile-image`

요청:

```json
{
  "profileImageUrl": "https://firebasestorage.googleapis.com/..."
}
```

응답:

```json
{
  "profileImageUrl": "https://firebasestorage.googleapis.com/..."
}
```

---

## 5) Disasters API

Prefix: `/api/v1/disasters`

## `POST /disasters/onboarding`

재난 온보딩(초기 영향 입력 + 사용자 재난 생성)

요청:

```json
{
  "disasterType": "FLOOD",
  "safetyStatus": "DAMAGED",
  "residenceStatus": "PARTIAL_DAMAGE",
  "injuryLevel": "MINOR",
  "damages": [true, false, true, false, true, false, false, false],
  "floodLevel": "FIRST_FLOOR",
  "waterDrainStatus": "PARTIAL_DRAINED"
}
```

응답:

```json
{
  "userDisasterId": 10,
  "impactId": 21,
  "onboardingRiskLevel": 2,
  "message": "피해 상황이 등록되었습니다"
}
```

노트:

- `damages` 배열은 재난 유형별 체크 인덱스를 사용합니다.
- 홍수/지진/화재는 각각 추가 필수 필드가 있으며 누락 시 `400 MISSING_REQUIRED_FIELD` 입니다.

## `GET /disasters/{userDisasterId}/recovery/stage`

최신 회복 단계 조회

응답:

```json
{
  "stageId": 1,
  "stageCode": "CHAOS",
  "stageName": "혼란기",
  "description": "상황을 받아들이는 것만으로도 버거운 상태예요."
}
```

## `GET /disasters/{userDisasterId}/recovery-graph`

회복 단계 이력(날짜 오름차순)

응답:

```json
{
  "userDisasterId": 10,
  "points": [
    {
      "date": "2026-06-01",
      "stageCode": "CHAOS",
      "stageName": "혼란기"
    },
    {
      "date": "2026-06-02",
      "stageCode": "STAGNANT",
      "stageName": "정체기"
    }
  ]
}
```

## `GET /disasters/{userDisasterId}/recovery/progress`

현재 회복 진행률 + 단계 정보

응답:

```json
{
  "userDisasterId": 10,
  "recoveryProgress": 42.5,
  "stageCode": "STAGNANT",
  "stageName": "정체기"
}
```

## `GET /disasters?page=0&size=20`

내 재난 목록 조회

응답:

```json
{
  "content": [
    {
      "userDisasterId": 10,
      "title": "2026년 집중호우",
      "disasterTypeCode": "FLOOD",
      "disasterTypeName": "홍수",
      "status": "ACTIVE",
      "occurredAt": "2026-02-24T09:00:00",
      "endedAt": null,
      "recoveryStage": {
        "stageCode": "CHAOS",
        "stageName": "혼란"
      },
      "recoveryProgress": 12.5
    }
  ],
  "page": 0,
  "size": 20,
  "totalElements": 1
}
```

## `GET /disasters/{userDisasterId}`

재난 상세 조회

응답:

```json
{
  "userDisasterId": 10,
  "title": "2026년 집중호우",
  "disasterType": {
    "disasterTypeId": 1,
    "disasterCode": "FLOOD",
    "name": "홍수"
  },
  "status": "ACTIVE",
  "occurredAt": "2026-02-24T09:00:00",
  "endedAt": null,
  "recoveryStage": {
    "stageCode": "CHAOS",
    "stageName": "혼란"
  },
  "recoveryProgress": 12.5,
  "impact": {
    "safetyStatus": "DAMAGED",
    "residenceStatus": "PARTIAL_DAMAGE",
    "injuryLevel": "MINOR",
    "canGoOut": true,
    "availableTime": "ONE_TO_THREE_HOURS"
  },
  "detail": {}
}
```

## `PATCH /disasters/{userDisasterId}`

재난 정보 부분 수정

요청 예시:

```json
{
  "title": "재난명 수정",
  "occurredAt": "2026-02-24T09:00:00",
  "impact": {
    "safetyStatus": "MINOR",
    "residenceStatus": "LIVABLE",
    "injuryLevel": "NONE",
    "canGoOut": true,
    "availableTime": "ONE_TO_THREE_HOURS"
  },
  "detail": {
    "floodLevel": "FIRST_FLOOR"
  }
}
```

응답:

```json
{
  "userDisasterId": 10,
  "message": "재난 정보가 수정되었습니다."
}
```

## `PATCH /disasters/{userDisasterId}/close`

ACTIVE 재난 종료/보관

요청:

```json
{
  "action": "CLOSE",
  "endedAt": "2026-02-28T11:30:00"
}
```

응답:

```json
{
  "userDisasterId": 10,
  "status": "EXPIRED",
  "endedAt": "2026-02-28T11:30:00",
  "message": "재난이 종료 처리되었습니다."
}
```

---

## 6) Checklists API

체크리스트 API는 별도 `/checklists` prefix가 아니라, 현재 구현상 `disasters` 하위 경로입니다.

Prefix: `/api/v1/disasters/{userDisasterId}`

추가로 아래 독립 경로도 구현되어 있습니다.

Prefix: `/api/v1/checklists`

## `POST /checklists/context`

체크리스트 컨텍스트(외출 가능 여부/가용 시간) 저장

요청:

```json
{
  "userDisasterId": 10,
  "userCondition": {
    "canGoOut": true,
    "availableTime": "ONE_TO_THREE_HOURS"
  }
}
```

응답:

```json
{
  "message": "상황 입력 완료"
}
```

## `POST /checklists/ai-generate`

AI 체크리스트 3개 생성

요청:

```json
{
  "userDisasterId": 10,
  "targetDate": "2026-06-09"
}
```

응답:

```json
{
  "items": [
    {
      "checklistItemId": 501,
      "title": "침수 피해 사진 정리 후 보관하기",
      "itemSourceType": "AI_GENERATED"
    },
    {
      "checklistItemId": 502,
      "title": "누전 위험 구역 전원 차단 여부 확인하기",
      "itemSourceType": "AI_GENERATED"
    },
    {
      "checklistItemId": 503,
      "title": "안전 상태 다시 한번 확인하기",
      "itemSourceType": "AI_GENERATED"
    }
  ]
}
```

노트:

- `GEMINI_API_KEY`가 없거나 생성 실패 시 fallback 3개 항목이 생성됩니다.

## `POST /disasters/{userDisasterId}/checklist`

체크리스트 항목 추가

요청:

```json
{
  "title": "보험사 접수 서류 준비",
  "checklistDate": "2026-02-24",
  "priority": 2
}
```

응답:

```json
{
  "checklistItemId": 501,
  "message": "체크리스트 항목이 추가되었습니다."
}
```

## `PATCH /disasters/{userDisasterId}/checklist/{checklistItemId}`

체크리스트 항목 수정

요청:

```json
{
  "title": "문구 수정",
  "checklistDate": "2026-02-24",
  "isCompleted": true,
  "priority": 1
}
```

응답:

```json
{
  "checklistItemId": 501,
  "message": "체크리스트 항목이 수정되었습니다."
}
```

## `PATCH /disasters/{userDisasterId}/checklist/{checklistItemId}/status`

완료 상태 변경

요청:

```json
{
  "isCompleted": true
}
```

응답:

```json
{
  "checklistItemId": 501,
  "isCompleted": true,
  "completedAt": "2026-02-24T09:41:00",
  "message": "완료 상태가 변경되었습니다."
}
```

검증:

- `isCompleted` 누락 시 `MISSING_REQUIRED_FIELD`
- bool 타입 아니면 `INVALID_FIELD_TYPE`

## `DELETE /disasters/{userDisasterId}/checklist/{checklistItemId}`

체크리스트 삭제(연결된 첨부 함께 삭제)

응답:

```json
{
  "checklistItemId": 501,
  "deletedAttachments": 7,
  "message": "체크리스트 항목이 삭제되었습니다."
}
```

## `GET /disasters/{userDisasterId}/checklist/{checklistItemId}`

체크리스트 상세 조회

응답:

```json
{
  "checklistItemId": 501,
  "title": "보험사 접수 서류 준비",
  "isCompleted": true,
  "completedAt": "2026-02-24T09:41:00",
  "checklistDate": "2026-02-24",
  "priority": 2,
  "isAiGenerated": false,
  "attachments": [
    {
      "attachmentId": 301,
      "attachmentType": "MEMO",
      "content": "메모 내용",
      "fileUrl": null,
      "originalFileName": null,
      "mimeType": null,
      "fileSize": null,
      "thumbnailUrl": null,
      "createdAt": "2026-02-24T09:00:00"
    }
  ]
}
```

## `GET /disasters/{userDisasterId}/checklist?date=...`
## `GET /disasters/{userDisasterId}/checklist?startDate=...&endDate=...`

일자/기간 체크리스트 조회

응답:

```json
{
  "userDisasterId": 10,
  "range": {
    "startDate": "2026-02-22",
    "endDate": "2026-02-28"
  },
  "completionRate": 59.8,
  "days": [
    {
      "checklistDate": "2026-02-24",
      "total": 6,
      "completed": 3,
      "items": [
        {
          "checklistItemId": 501,
          "title": "보험사 접수 서류 준비",
          "isCompleted": true,
          "priority": 2,
          "isAiGenerated": false,
          "attachmentSummary": {
            "MEMO": 1,
            "IMAGE": 2,
            "FILE": 0
          }
        }
      ]
    }
  ]
}
```

## `GET /disasters/{userDisasterId}/archives?type=ALL&date=...&cursor=...&limit=20`

아카이빙 통합 조회(커서 기반)

쿼리:

- `type`: `ALL|MEMO|IMAGE|FILE` (default `ALL`)
- `date`: `YYYY-MM-DD` optional
- `cursor`: optional
- `limit`: default 20, 허용 1~50

응답:

```json
{
  "userDisasterId": 10,
  "items": [
    {
      "attachmentId": 302,
      "checklistItemId": 501,
      "checklistItemTitle": "보험사 접수 서류 준비",
      "attachmentType": "IMAGE",
      "fileUrl": "https://firebasestorage.googleapis.com/...",
      "originalFileName": "damage_photo_01.jpg",
      "mimeType": "image/jpeg",
      "thumbnailUrl": "https://firebasestorage.googleapis.com/.../thumb.jpg",
      "checklistDate": "2026-02-24",
      "createdAt": "2026-02-24T09:05:00"
    }
  ],
  "nextCursor": "eyJpZCI6MzAyfQ==",
  "hasMore": true
}
```

---

## 7) Home API

Prefix: `/api/v1/home`

## `POST /home/daily-status`

오늘 상태 체크 제출

요청:

```json
{
  "emotionScore": 3,
  "energyScore": 2,
  "activityScore": 1,
  "recoveryScore": 2,
  "needScore": 1
}
```

응답:

```json
{
  "dailyCheckId": 1001,
  "totalScore": 9,
  "message": "상태 체크 완료"
}
```

## `GET /home/daily-status`

오늘 상태 체크 조회

응답(체크 없음):

```json
{
  "checked": false,
  "message": "오늘 상태 체크가 아직 없습니다."
}
```

응답(체크 있음):

```json
{
  "checked": true,
  "dailyCheckId": 1001,
  "emotionScore": 3,
  "energyScore": 2,
  "activityScore": 1.0,
  "recoveryScore": 2,
  "needScore": 1.0,
  "totalScore": 9,
  "message": "오늘 상태 체크 조회 완료"
}
```

## `GET /home/summary`

홈 요약 조회

응답:

```json
{
  "userDisasterId": 10,
  "userName": "홍길동",
  "disasterTitle": "2026년 집중호우",
  "disasterTypeName": "홍수",
  "occurredAt": "2026-02-24T09:00:00",
  "recoveryStageName": "혼란",
  "recoveryProgress": 12.5,
  "dailyStatusChecked": true,
  "todayTotalTasks": 6,
  "todayCompletedTasks": 3,
  "todayCompletionRate": 50.0
}
```

주의:

- 현재 코드 기준으로 `userName`, `occurredAt`이 실제 응답에 포함됩니다.
- `occurredAt`은 ISO8601 문자열 형태입니다.

## `GET /home/today-tasks`

오늘 할 일 상위 3개

응답:

```json
{
  "totalCount": 3,
  "items": [
    {
      "checklistItemId": 501,
      "title": "보험사 접수 서류 준비",
      "priority": 1,
      "isCompleted": false,
      "isAiGenerated": true
    }
  ]
}
```

주의:

- `totalCount`는 "오늘 전체 할 일 개수"가 아니라 **현재 응답의 `items` 길이**입니다.
- 따라서 `/home/today-tasks`에서는 최대 3이며, 전체 개수가 필요하면 `/home/summary`의 `todayTotalTasks`를 사용하세요.

## `GET /home/today-tasks/full`

오늘 할 일 전체

응답 구조는 `/home/today-tasks`와 동일하며 `items`만 전체 길이로 반환됩니다.

---

## 8) 프론트 구현 시 주의사항

- 체크리스트는 `/disasters/{userDisasterId}/checklist*`와 `/checklists/context`, `/checklists/ai-generate`를 함께 사용합니다.
- Home API는 camelCase 응답(`todayTotalTasks`)입니다.
- `GET /home/summary`는 `userName`, `occurredAt`을 포함합니다.
- checklist 상세의 `isAiGenerated`는 `item_source_type == "AI_GENERATED"` 기준입니다.
- archives `cursor`는 서버가 만든 base64 문자열을 그대로 다음 요청에 넘겨야 합니다.
- 일부 유효성 오류는 라우터에서 `400`, 일부는 Pydantic 기본 검증으로 `422`가 내려올 수 있습니다.

---

## 9) 빠른 테스트 순서 (권장)

1. `POST /api/v1/auth/login`
2. 받은 `accessToken`으로 Authorization 헤더 세팅
3. `GET /api/v1/disasters`
4. `POST /api/v1/disasters/{userDisasterId}/checklist`
5. `PATCH /api/v1/disasters/{userDisasterId}/checklist/{checklistItemId}/status`
6. `GET /api/v1/disasters/{userDisasterId}/checklist/{checklistItemId}`

