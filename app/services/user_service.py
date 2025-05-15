from typing import List, Optional
from sqlmodel import Session, select
from app.models.user_model import User
from app.schemas.user import UserCreate, UserUpdate
from app.core.security import get_password_hash

class UserService:
    def create(self, db: Session, user_create: UserCreate) -> User:
        hashed_password = get_password_hash(user_create.password)
        user = User(
            email=user_create.email,
            username=user_create.username,
            full_name=user_create.full_name,
            hashed_password=hashed_password
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user

    def get(self, db: Session, user_id: int) -> Optional[User]:
        return db.get(User, user_id)

    def get_all(self, db: Session) -> List[User]:
        return db.exec(select(User)).all()

    def update(self, db: Session, user_id: int, user_update: UserUpdate) -> Optional[User]:
        user = self.get(db, user_id)
        if not user:
            return None
        
        update_data = user_update.dict(exclude_unset=True)
        if "password" in update_data:
            update_data["hashed_password"] = get_password_hash(update_data.pop("password"))
        
        for field, value in update_data.items():
            setattr(user, field, value)
        
        db.add(user)
        db.commit()
        db.refresh(user)
        return user

    def delete(self, db: Session, user_id: int) -> Optional[User]:
        user = self.get(db, user_id)
        if not user:
            return None
        db.delete(user)
        db.commit()
        return user
