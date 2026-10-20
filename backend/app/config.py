from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "sqlite:///./library.db"
    jwt_secret: str = "dev-only-secret-please-change-me-0123456789"
    jwt_expire_minutes: int = 60 * 24
    bcrypt_rounds: int = 12
    upload_dir: str = "uploads"
    max_upload_bytes: int = 2 * 1024 * 1024
    admin_username: str = "admin"
    admin_password: str = "admin123"
    cors_origins: list[str] = ["http://localhost:5173"]


settings = Settings()
