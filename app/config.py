from typing import Literal
from functools import lru_cache
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    ENV: Literal["test", "dev", "prod"] = "dev"
    LOG_LEVEL: Literal["CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG", "TRACE"] = "INFO"
    DB_URL: str = ""  # Empty by default - validation only happens on server init
    APP_DEBUG: bool = True
    APP_DESCRIPTION: str = "Clean Architecture Python Backend Template"
    APP_TITLE: str = "Python Template"
    APP_VERSION: str = "0.0.1"
    SERVER_HOST: str = "0.0.0.0"
    SERVER_PORT: int = 3000
    SERVER_RELOAD: bool = True
    JWT_SECRET_KEY: str = "unsafe"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    # A aplicação não lê .env implicitamente.
    # Cada contexto (dev/test/prod) deve injetar as variáveis explicitamente
    # via Docker Compose (--env-file) ou shell export.
    model_config = SettingsConfigDict(env_file=None, extra="ignore")

    @field_validator("DB_URL")
    @classmethod
    def validate_db_url_on_runtime(cls, db_url: str) -> str:
        """
        DB_URL validation is deferred to runtime.
        This prevents ValidationError during test collection for unit tests,
        which don't need database access.
        
        Actual validation happens in app.main.create_app() before server starts.
        """
        return db_url

    def validate_for_server_start(self) -> None:
        """
        Call this method explicitly when starting the server to validate DB_URL.
        This ensures database is only required when the server actually runs.
        """
        if not self.DB_URL:
            raise ValueError(
                "Database URL is required to start the server. "
                "Set DB_URL environment variable."
            )


@lru_cache()
def get_settings() -> Settings:
    return Settings()
