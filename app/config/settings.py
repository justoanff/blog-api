from pydantic import computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8')
    PROJECT_NAME: str = "FastAPI Application"
    VERSION: str = "1.0.0"
    DESCRIPTION: str = "FastAPI application with SQLModel and PostgreSQL"
    API_V1_STR: str = "/api/v1"
    
    # Security
    ACCESS_TOKEN_SECRET_KEY = "your_super_long_random_access_secret"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    REFRESH_TOKEN_SECRET_KEY: str = "your-refresh-secret-key-here" # NÊN KHÁC SECRET_KEY
    REFRESH_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 ngày
    
    # Database
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_SERVER: str
    POSTGRES_DB: str
    
    @computed_field
    @property
    def DATABASE_URL(self) -> str:
        return f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_SERVER}/{self.POSTGRES_DB}"
    
    # Redis Configuration
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: Optional[str] = None

    @computed_field
    @property
    def REDIS_URL(self) -> str:
        if self.REDIS_PASSWORD:
            return f"redis://:{self.REDIS_PASSWORD}@{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
    
from functools import lru_cache

@lru_cache()
def get_settings() -> Settings:
    return Settings()
current_settings = get_settings()
print(current_settings.DATABASE_URL)