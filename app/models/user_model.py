from typing import List, TYPE_CHECKING
from app.models.base_model import BaseModel
from sqlmodel import Field, Relationship

if TYPE_CHECKING:
    from .post_model import Post
    from .refresh_token_model import RefreshToken
    
class UserBase(BaseModel):
    username: str = Field(unique=True, index=True, max_length=50)
    is_active: bool = Field(default=True)
    email: str = Field(unique=True, index=True, max_length=255)
class User(UserBase, table=True):
    hashed_password: str = Field(max_length=255)
    posts: List["Post"] = Relationship(back_populates="owner", sa_relationship_kwargs={"lazy": "selectin"})
    refresh_tokens: List["RefreshToken"] = Relationship(back_populates="user", sa_relationship_kwargs={"cascade": "all, delete-orphan"})
    