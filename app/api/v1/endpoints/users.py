from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session
from typing import List
from app.config.database import get_session
from app.schemas.user import UserCreate, UserRead, UserUpdate
from app.services.user_service import UserService

router = APIRouter()
user_service = UserService()

@router.post("/", response_model=UserRead)
def create_user(user: UserCreate, db: Session = Depends(get_session)):
    return user_service.create(db, user)

@router.get("/", response_model=List[UserRead])
def get_users(db: Session = Depends(get_session)):
    return user_service.get_all(db)

@router.get("/{user_id}", response_model=UserRead)
def get_user(user_id: int, db: Session = Depends(get_session)):
    user = user_service.get(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@router.put("/{user_id}", response_model=UserRead)
def update_user(user_id: int, user: UserUpdate, db: Session = Depends(get_session)):
    updated_user = user_service.update(db, user_id, user)
    if not updated_user:
        raise HTTPException(status_code=404, detail="User not found")
    return updated_user

@router.delete("/{user_id}")
def delete_user(user_id: int, db: Session = Depends(get_session)):
    user = user_service.delete(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return {"message": "User deleted successfully"}
