from typing import Optional, TYPE_CHECKING
from uuid import UUID
from datetime import datetime, timezone

from sqlmodel import Field, Relationship, SQLModel, Column, DateTime, String, func
from .base_model import BaseModel

if TYPE_CHECKING:
    from .user_model import User
    
class RefreshToken(BaseModel):
    
    token_hash: str = Field(sa_column=Column(String(128), unique=True, index=True, nullable=False))
    
    expires_at: datetime = Field(sa_column=Column(DateTime(timezone=True), nullable=False))
    
    is_revoked: bool = Field(default=False, nullable=False)
    
    user_agent: Optional[str] = Field(default=None, max_length= 512)
    ip_address: Optional[str] = Field(default=None, max_length=45)
    
    family: Optional[UUID] = Field(default=None, index=True)
    
    user_id: UUID = Field(foreign_key="user.id", index=True, nullable=False)
    
class RefreshToken(RefreshToken, table=True):
    
    user: Optional["User"] = Relationship(back_populates="refresh_tokens")