from pydantic import BaseModel, ConfigDict, EmailStr
from typing import Optional, List
from uuid import UUID
from datetime import datetime

from app.schemas.post_schema import PostResponse

class UserBase(BaseModel):
    username: str
    email: EmailStr
    is_active: bool
    
class UserCreate(UserBase):
    password: str

class UserUpdate(UserBase):
    username: Optional[str] = None
    email: Optional[EmailStr] = None
    password: Optional[str] = None
    is_active: Optional[bool] = None
    
class UserResponse(UserBase):
    id: UUID
    created_at: datetime
    updated_at: datetime
    posts: List["PostResponse"] = [] # Sử dụng forward reference string "PostResponse"
    model_config = ConfigDict(from_attributes=True)