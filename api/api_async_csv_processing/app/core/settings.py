from functools import lru_cache
from pydantic import Field
from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    postgres_user: str = Field(..., env="postgres_user")
    postgres_password: str = Field(..., env="postgres_password")
    postgres_host: str = Field(..., env="postgres_host")
    postgres_port: str = Field(..., env="postgres_port")
    postgres_db: str = Field(..., env="transactions_db")

    cors_origins: List[str] = [
        "http://localhost:4200",
    ]

    class Config:
        env_file = ".env"  # Optional: load from .env if needed
        extra = 'allow'


@lru_cache
def get_settings() -> Settings:
    return Settings()

settings = get_settings()
