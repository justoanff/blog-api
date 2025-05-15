from fastapi import FastAPI
from fastapi.concurrency import asynccontextmanager
from app.api.v1.router import api_router
from app.core.config import get_settings
from app.core.redis_client import close_redis_client, get_redis_client

settings = get_settings()

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description=settings.DESCRIPTION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

app.include_router(api_router, prefix=settings.API_V1_STR)

@app.get("/")
async def root():
    return {"message": "Welcome to FastAPI application"}

from fastapi import FastAPI
from contextlib import asynccontextmanager
from app.core.redis_client import get_redis_client, close_redis_client # Import

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("INFO:     Starting up application...")
    await get_redis_client() # Khởi tạo (hoặc đảm bảo có) Redis client
    yield
    print("INFO:     Shutting down application...")
    await close_redis_client() # Đóng Redis client

app = FastAPI(lifespan=lifespan)