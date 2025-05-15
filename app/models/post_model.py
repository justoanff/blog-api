from typing import Optional, TYPE_CHECKING
from uuid import UUID
from app.models.base_model import BaseModel
from sqlmodel import Field, Relationship

if TYPE_CHECKING:
    from .user_model import User
    
class PostBase(BaseModel):
    title: str = Field(index=True, max_length=200)
    content: str = Field(default= None)
    
class Post(PostBase, table = True):
    owner_id: UUID = Field(foreign_key="user.id", index=True)
    owner: Optional["User"] = Relationship(back_populates="posts")
    
    