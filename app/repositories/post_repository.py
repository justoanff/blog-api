from typing import List, Optional
from uuid import UUID
from sqlmodel import Session, select

from app.models.post_model import Post
from app.schemas.post_schema import PostCreate, PostUpdate
from app.repositories.base_repository import BaseRepository

class PostRepository(BaseRepository[Post, PostCreate, PostUpdate]):
    def create_with_owner(
        self, db: Session, *, obj_in: PostCreate, owner_id: UUID
    ) -> Post:
        db_obj = Post.model_validate(obj_in, update={"owener_id": owner_id})
        
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj
    
    def get_multi_by_owner(
        self, db: Session, *, owner_id: UUID, skip: int = 0, limit: int = 100
    ) -> List[Post]:
        
        statement = (
            select(Post)
            .where(Post.owner_id == owner_id)
            .offset(skip)
            .limit(limit)
        )
        return db.exec(statement).all()
    
post_repo = PostRepository(Post)