from typing import Optional, Dict, Any, Union
from uuid import UUID
from sqlmodel import Session, select

from app.models.user_model import User
from app.schemas.user_schema import UserCreate, UserUpdate
from app.repositories.base_repository import BaseRepository
from app.core.security import get_password_hash

class UserRepository(BaseRepository[User, UserCreate, UserUpdate]):
    def get_by_username(self, db: Session, *, username: str) -> Optional[User]:
        statement = select(User).where(User.username == username)
        return db.exec(statement).first()
    
    def get_by_email(self, db: Session, *, email: str) -> Optional[User]:
        statement = select(User).where(User.email == email)
        return db.exec(statement).first()
    
    def create(self, db: Session, *, obj_in: UserCreate) -> User:
        
        user_data_for_model = obj_in.model_dump(exclude={"password"})
        hashed_password = get_password_hash(obj_in.password)
        db_obj = User(**user_data_for_model, hashed_password=hashed_password)
        
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj
    
    def update(
        self,
        db: Session,
        *,
        db_obj: User,
        obj_in: Union[UserUpdate, Dict[str, Any]]
    ) -> User:
        update_data = {}
        if isinstance(obj_in, dict):
            update_data=obj_in
        else:
            update_data = obj_in.model_dump(exclude_unset=True)
        
        if "password" in update_data and update_data["password"]:
            hashed_password = get_password_hash(update_data["password"])
            db_obj.hashed_password = hashed_password
            del update_data["password"]
        
        return super().update(db, db_obj=db_obj, obj_in=update_data)
    
user_repo = UserRepository(User)