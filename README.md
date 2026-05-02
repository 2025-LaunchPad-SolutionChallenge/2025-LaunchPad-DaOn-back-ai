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
