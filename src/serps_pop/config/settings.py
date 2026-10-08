from functools import lru_cache

from pydantic import Field, SecretStr, model_validator
from urllib.parse import urlsplit
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="SERPS_", env_file=".env", extra="ignore", hide_input_in_errors=True)

    env: str = "development"
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    database_url: str = Field(repr=False)
    jwt_secret: SecretStr
    jwt_issuer: str = "serps-pop"
    jwt_audience: str = "serps-api"
    access_token_minutes: int = Field(default=10, ge=1, le=20)
    refresh_token_days: int = 7
    cors_origins: str = "http://localhost:3000,http://127.0.0.1:3000"
    frontend_build_id: str = "serps-web-1.0-rc1-s4c"
    backend_build_id: str = "serps-api-1.0-rc1-s4c"
    demo_policy_controls: bool = False


    @model_validator(mode='after')
    def validate_hosted_configuration(self):
        if self.env in {'staging', 'production'}:
            secret = self.jwt_secret.get_secret_value()
            if len(secret) < 32 or secret.lower().startswith(('replace-', 'your-')):
                raise ValueError('Hosted environments require a unique JWT secret of at least 32 characters.')
            if self.demo_policy_controls:
                raise ValueError('Demonstration policy controls must remain disabled in hosted environments.')
            if not self.database_url.startswith('postgresql+psycopg://'):
                raise ValueError('Hosted environments require an explicit PostgreSQL psycopg URL.')
            origins = [origin.strip() for origin in self.cors_origins.split(',') if origin.strip()]
            if not origins:
                raise ValueError('At least one explicit CORS origin is required.')
            for origin in origins:
                parsed = urlsplit(origin)
                local = parsed.hostname in {'localhost', '127.0.0.1', '::1'}
                if (not parsed.hostname or '*' in origin or parsed.username or parsed.password
                        or parsed.query or parsed.fragment or parsed.path not in {'', '/'}
                        or (parsed.scheme != 'https' and not (local and parsed.scheme == 'http'))):
                    raise ValueError('CORS must contain exact HTTPS origins (HTTP only for loopback validation).')
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
