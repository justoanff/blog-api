from pydantic import BaseModel, ConfigDict
from typing import Optional
from uuid import UUID
from datetime import datetime

from .user_schema import UserResponse

class PostBase(BaseModel):
    title: str
    content: Optional[str] = None
    
class PostCreate(PostBase):
    pass

class PostUpdate(PostBase):
    title: Optional[str] = None
    content: Optional[str] = None
    
class PostResponse(PostBase):
    id: UUID
    created_at: datetime
    updated_at: datetime
    owner_id: UUID
    owner: Optional[UserResponse] = None
    model_config = ConfigDict(from_attributes=True)