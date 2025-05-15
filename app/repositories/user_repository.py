from typing import Optional, Dict, Any, Union
from uuid import UUID
from sqlmodel import Session, select

from app.models.user_model import User
from app.schemas.user_schema import UserCreate, UserUpdate
from app.repositories.base_repository import BaseRepository

class UserRepository(BaseRepository[User, UserCreate, UserUpdate]):
    def get_by_username(self, db: Session, *, username: str) -> Optional[User]:
        statement = select(User).where(User.username == username)
        return db.exec(statement).first()
    
    def get_by_email(self, db: Session, *, email: str) -> Optional[User]:
        statement = select(User).where(User.email == email)
        return db.exec(statement).first()