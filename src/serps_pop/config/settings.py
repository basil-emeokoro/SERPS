from functools import lru_cache

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="SERPS_", env_file=".env", extra="ignore")

    env: str = "development"
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    database_url: str
    jwt_secret: SecretStr
    jwt_issuer: str = "serps-pop"
    jwt_audience: str = "serps-api"
    access_token_minutes: int = Field(default=10, ge=1, le=20)
    refresh_token_days: int = 7
    cors_origins: str = "http://localhost:3000,http://127.0.0.1:3000"
    frontend_build_id: str = "serps-web-1.0-rc1-s4c"
    backend_build_id: str = "serps-api-1.0-rc1-s4c"
    demo_policy_controls: bool = False


@lru_cache
def get_settings() -> Settings:
    return Settings()
