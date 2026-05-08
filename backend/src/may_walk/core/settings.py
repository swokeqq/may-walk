"""Настройки приложения и окружения."""

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Настройки приложения."""

    model_config = SettingsConfigDict(
        env_file='.env',
        env_file_encoding='utf-8',
        extra='ignore',
    )

    debug: bool = False
    database_url: str
    auth_cookie_secure: bool = True
    auth_cookie_samesite: str = 'lax'
    auth_session_ttl_hours: int = 24
    osrm_url: str
    osrm_timeout_s: float = Field(default=30.0, gt=0)
    osrm_radius_m: float = Field(default=25.0, gt=0)
    osrm_max_matching_size: int = Field(default=500, ge=2)


settings = Settings()
