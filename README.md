# FastAPI Backend Boilerplate

FastAPI + MySQL + SQLAlchemy + Alembic 기본 세팅입니다.

## 1) 가상환경 생성 및 의존성 설치

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## 2) 환경 변수 설정

`.env.example`을 복사해서 `.env`를 생성하세요.

```bash
cp .env.example .env
```

## 3) 마이그레이션 파일 생성/적용

```bash
alembic revision --autogenerate -m "init"
alembic upgrade head
```

## 4) 서버 실행

```bash
uvicorn app.main:app --reload
```

## Docker Compose로 실행

```bash
docker compose up -d --build
```

앱 컨테이너 시작 시 `alembic upgrade head`가 먼저 수행된 뒤 API가 실행됩니다.

## 기본 엔드포인트

- `GET /health`
- `GET /api/users`
- `POST /api/users`

## 예상 
```plaintext
app/
│
├── main.py
├── config.py                    # pydantic-settings, .env 파싱
├── database.py                  # engine, SessionLocal, get_db
│
├── common/
│   ├── base_entity.py           # BaseEntity(created_at, updated_at)
│   ├── base_model.py            # SQLAlchemy DeclarativeBase
│   ├── exceptions.py            # 커스텀 예외 (NotFoundError, UnauthorizedError 등)
│   ├── dependencies.py          # Depends(get_db), Depends(get_current_user)
│   ├── security.py              # JWT 생성/검증, Firebase 토큰 검증
│   └── response.py              # 공통 Response 포맷 (code, message, data)
│
├── domain/
│   ├── auth/
│   │   ├── entity.py            # AuthToken, UserCredential (value object)
│   │   ├── repository.py        # AuthRepository (abstract)
│   │   └── service.py           # register, login, refresh, withdraw 로직
│   │
│   ├── user/
│   │   ├── entity.py            # User, UserSetting, UserResidence
│   │   ├── repository.py        # UserRepository (abstract)
│   │   └── service.py           # 프로필 수정, 식물 상태 계산 로직
│   │
│   ├── disaster/
│   │   ├── entity.py            # UserDisaster, DisasterImpact,
│   │   │                        # EarthquakeImpact, FloodImpact 등
│   │   ├── repository.py
│   │   └── service.py           # 재난 등록, 상태변경, 회복 그래프 계산
│   │
│   ├── home/
│   │   ├── entity.py            # DailyStatusCheck, HomeSummary (value object)
│   │   ├── repository.py
│   │   └── service.py           # 홈 요약 집계, 상태체크 조회/수정
│   │
│   ├── checklist/
│   │   ├── entity.py            # ChecklistItem, ArchiveItem, ArchiveFile
│   │   ├── repository.py
│   │   └── service.py           # 체크리스트 CRUD, 주간달성률, 아카이브
│   │
│   └── community/
│       ├── entity.py            # CommunityPost, CommunityProfile,
│       │                        # Comment, PostAttachment, PostLink
│       ├── repository.py
│       └── service.py           # 게시글/댓글 CRUD, 스크랩, 긴급요청 쿼터
│
├── infrastructure/
│   ├── models/
│   │   ├── user_model.py        # Users, UserAuthProvider, UserResidence,
│   │   │                        # UserSetting
│   │   ├── disaster_model.py    # UserDisaster, DisasterType, DisasterImpact,
│   │   │                        # EarthquakeImpact, TyphoonImpact,
│   │   │                        # FireImpact, FloodImpact
│   │   ├── recovery_model.py    # RecoveryStageMaster, RecoveryOutput,
│   │   │                        # RecoveryFeature
│   │   ├── checklist_model.py   # ChecklistItem, ArchiveItem, ArchiveFile
│   │   └── community_model.py   # CommunityPost, CommunityProfile,
│   │                            # CommunityCategory, PostLink,
│   │                            # PostAttachment, DailyStatusCheck
│   │
│   └── repositories/
│       ├── auth_repository.py
│       ├── user_repository.py
│       ├── disaster_repository.py
│       ├── home_repository.py
│       ├── checklist_repository.py
│       └── community_repository.py
│
└── interface/
    ├── auth/
    │   ├── router.py            # /api/v1/auth/*
    │   └── schema.py            # RegisterRequest, LoginRequest,
    │                            # TokenResponse, LocationSearchResponse
    ├── user/
    │   ├── router.py            # /api/v1/users/me/*
    │   └── schema.py            # ProfileResponse, PlantStatusResponse
    ├── disaster/
    │   ├── router.py            # /api/v1/disasters/*
    │   └── schema.py            # DisasterResponse, RecoveryGraphResponse
    ├── home/
    │   ├── router.py            # /api/v1/home/*
    │   └── schema.py            # DailyStatusResponse, HomeSummaryResponse
    ├── checklist/
    │   ├── router.py            # /api/v1/checklists/*
    │   └── schema.py            # ChecklistItemResponse, ArchiveResponse
    └── community/
        ├── router.py            # /api/v1/community/*
        └── schema.py            # PostResponse, CommentResponse, ProfileResponse
    ```