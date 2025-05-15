from datetime import datetime, timedelta, timezone
from typing import Any, Union, Optional
from uuid import uuid4

from jose import jwt, JWTError
from passlib.context import CryptContext
import redis

from app.config.settings import get_settings
from app.schemas.token_schema import TokenPayload

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
settings = get_settings()

ALGORITHM = settings.ALGORITHM
ACCESS_TOKEN_SECRET_KEY = settings.ACCESS_TOKEN_SECRET_KEY
ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES

REFRESH_TOKEN_SECRET_KEY = settings.REFRESH_TOKEN_SECRET_KEY
REFRESH_TOKEN_EXPIRE_MINUTES = settings.REFRESH_TOKEN_EXPIRE_MINUTES

REVOKED_TOKENS_REDIS_PREFIX = "revoked_tokens:"

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def _create_token(
    subject: Union[str, Any],
    expires_delta_minutes: int,
    secret_key: str,
    token_type: str,
    additional_payload: Optional[dict] = None,
) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=expires_delta_minutes)
    jti = str(uuid4())
    to_encode = {
        "exp": expire,
        "sub": str(subject),
        "jti": jti,
        "type": token_type
    }
    if additional_payload:
        to_encode.update(additional_payload)
    encoded_jwt = jwt.encode(to_encode, secret_key, algorithm=ALGORITHM)
    return encoded_jwt

def create_access_token(subject: Union[str, Any]) -> str:
    return _create_token(
        subject=subject,
        expires_delta_minutes=ACCESS_TOKEN_EXPIRE_MINUTES,
        secret_key= ACCESS_TOKEN_SECRET_KEY,
        token_type="access"
    )
    
def create_refresh_token(subject: Union[str, Any]) -> str:
    return _create_token(
        subject=subject,
        expires_delta_minutes=REFRESH_TOKEN_EXPIRE_MINUTES,
        secret_key=REFRESH_TOKEN_SECRET_KEY,
        token_type="refresh"
    )

async def _decode_and_validate_token(
    token: str,
    secret_key: str,
    expected_token_type: str,
    redis_client: redis.Redis
) -> Optional[TokenPayload]:
    try:
        payload = jwt.decode(token, secret_key, algorithms=[ALGORITHM])
        token_jti: Optional[str] = payload.get("jti")
        token_type: Optional[str] = payload.get("type")
        subject: Optional[str] = payload.get("sub")
        expires_at_timestamp: Optional[int] = payload.get("exp")
        
        if not all([token_jti, token_type, subject, expires_at_timestamp]):
            return None
        
        if token_type != expected_token_type:
            return None
        
        is_revoked = await redis_client.exists(f"{REVOKED_TOKENS_REDIS_PREFIX}{token_jti}")
        if is_revoked:
            return None
        
        return TokenPayload(sub=subject, jti=token_jti, exp=expires_at_timestamp, type=token_type)
    except JWTError:
        return None
    except Exception:
        return None
    
async def decode_access_token(token: str, redis_client: redis.Redis) -> Optional[TokenPayload]:
    return await _decode_and_validate_token(
        token=token,
        secret_key=ACCESS_TOKEN_SECRET_KEY,
        expected_token_type="access",
        redis_client=redis_client       
    )

async def decode_refresh_token(token: str, redis_client: redis.Redis) -> Optional[TokenPayload]:
    return await _decode_and_validate_token(
        token=token,
        secret_key=REFRESH_TOKEN_SECRET_KEY,
        expected_token_type="refresh",
        redis_client=redis_client
    )

async def revoke_token(
    jti: str,
    expires_at_timestamp: int,
    redis_client: redis.Redis
):
    now_timestamp = int(datetime.now(timezone.utc).timestamp())
    ttl_seconds = max(0, expires_at_timestamp - now_timestamp)
    
    if ttl_seconds > 0:
        try: 
            await redis_client.setex(f"{REVOKED_TOKENS_REDIS_PREFIX}{jti}", ttl_seconds, "revoked")
            print(f"Token JTI {jti} revoked. Will expire in Redis in {ttl_seconds} seconds")
        except Exception as e:
            print(f"Error revoking token {jti}: {e}")
    else:
        print(f"Token JTI {jti} already expired. Not added to Redis blacklist")
        return True
