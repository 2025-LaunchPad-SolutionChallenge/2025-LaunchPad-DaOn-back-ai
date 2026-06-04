from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # ── App ───────────────────────────────────────────────────────────────
    APP_NAME: str = "Quad API"
    DEBUG: bool = False

    # ── Database (.env 의 MYSQL_* 과 1:1 매핑) ──────────────────────────────
    MYSQL_HOST: str
    MYSQL_PORT: int = 3306
    MYSQL_USER: str
    MYSQL_PASSWORD: str
    MYSQL_DB: str

    @property
    def DATABASE_URL(self) -> str:
        return (
            f"mysql+aiomysql://{self.MYSQL_USER}:{self.MYSQL_PASSWORD}"
            f"@{self.MYSQL_HOST}:{self.MYSQL_PORT}/{self.MYSQL_DB}"
        )

    # ── JWT ───────────────────────────────────────────────────────────────
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30

    # ── Firebase ──────────────────────────────────────────────────────────
    FIREBASE_CREDENTIALS_PATH: str
    FIREBASE_STORAGE_BUCKET: str = ""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
