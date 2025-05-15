from uuid import UUID
from fastapi import HTTPException, status
from sqlmodel import Session

from app.models.post_model import Post
from app.models.user_model import User
from app.repositories.post_repository import post_repo
from app.schemas.post_schema import PostCreate

class PostService:
    def __init__(self, repository=post_repo):
        self.repository = repository
        
    def get_post_by_id(self, db: Session, post_id: UUID) -> Post:
        post = self.repository.get(db, id=post_id)
        
        if not post:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")
        return post
    
    def get_posts(self, db: Session, skip: int = 0, limit: int = 100) -> list[Post]:
        return self.repository.get_multi(db, skip=skip, limit=limit)
    
    def get_posts_by_owner(
        self, db: Session, *, owner_id: UUID, skip: int = 0, limit: int = 100
    ) -> list[Post]:
        return self.repository.get_multi_by_owner(db, owner_id=owner_id, skip=skip, limit=limit)
    
    def create_post(
        self, db: Session, *, post_in: PostCreate, current_user: User
    ) -> Post:
        new_post = self.repository.create_with_owner(db, obj_in=post_in, owner_id=current_user.id)
        return new_post
    
    def update_post(
        self, db: Session, *, post_id_to_update: UUID, post_in: PostCreate, current_user: User
    ) -> Post:
        db_post_to_update = self.get_post_by_id(db, post_id=post_id_to_update)
        if not db_post_to_update:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions to update this post")
        
        updated_post = self.repository.update(db, db_obj=db_post_to_update, obj_in=post_in)
        return updated_post
    
    def delete_post(
        self, db: Session, *, post_id_to_delete: UUID, current_user: User
    ) -> Post:
        db_post_to_delete = self.get_post_by_id(db, post_id=post_id_to_delete)
        
        if db_post_to_delete.owner_id != current_user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions to delete this post")
        
        deleted_post_data = self.repository.remove(db, id=post_id_to_delete)
        if not deleted_post_data:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to delete post")
        return deleted_post_data
    
post_service = PostService()