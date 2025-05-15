from typing import List, Optional, Dict, Any, Union
from uuid import UUID
from sqlmodel import Session
from fastapi import HTTPException, status

from app.repositories.user_repository import user_repo
from app.schemas.user_schema import UserCreate, UserUpdate, UserResponse
from app.models.user_model import User
from app.core.security import verify_password

class UserService:
    def __init__(self, repository=user_repo):
        self.repository = repository
        
    def get_user_by_id(self, db: Session, user_id: UUID) -> Optional[User]:
        return self.repository.get(db, id=user_id)
    
    def get_user_by_username(self, db: Session, username: str) -> Optional[User]:
        return self.repository.get_by_username(db, username=username)
    
    def get_user_by_email(self, db: Session, email: str) -> Optional[User]:
        return self.repository.get_by_email(db, email=email)
    
    def get_users(
        self, db: Session, *, skip: int = 0, limit: int = 100
    ) -> List[User]:
        return self.repository.get_multi(db, skip=skip, limit=limit)
    
    def create_user(self, db: Session, *, user_in: UserCreate) -> User:
        existing_user_by_username = self.repository.get_by_username(db, username=user_in.username)
        if existing_user_by_username:
            raise HTTPException(
                 status_code=status.HTTP_400_BAD_REQUEST,
                 detail="Username already exists"
            )
        existing_user_by_email = self.repository.get_by_email(db, email=user_in.email)
        if existing_user_by_email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already exists"
            )
        new_user = self.repository.create(db, obj_in=user_in)
        return new_user
    
    def update_user(
        self, db: Session, *, user_id_to_update: UUID, user_in: UserUpdate, current_user: User
    ) -> User:
        db_user_to_update = self.repository.get(db, id=user_id_to_update)
        if not db_user_to_update:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        
        if db_user_to_update.id != current_user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions")
        
        if user_in.username and user_in.username != db_user_to_update.username:
            existing_user = self.repository.get_by_username(db, username=user_in.username)
            if existing_user and existing_user.id != user_id_to_update:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Username already taken"
                )
        
        if user_in.email and user_in.email != db_user_to_update.email:
            existing_user = self.repository.get_by_email(db, email=user_in.email)
            if existing_user and existing_user.id != user_id_to_update:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email already taken"
                )
        
        updated_user = self.repository.update(db, db_obj=db_user_to_update, obj_in=user_in)
        return updated_user
    
    def authenticate_user(
        self, db: Session, *, username: str, password_in: str
    ) -> Optional[User]:
        user = self.repository.get_by_username(db, username=username)
        if not user:
            return None
        if not user.is_active:
            return None
        if not verify_password(password_in, user.hashed_password):
            return None
        return user
    
user_service = UserService()