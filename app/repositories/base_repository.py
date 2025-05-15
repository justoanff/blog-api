from typing import Any, Dict, Generic, TypeVar, Type, Optional, List, Union
from sqlmodel import SQLModel, select, Session
from uuid import UUID

from app.models.base_model import BaseModel

ModelType = TypeVar("ModelType", bound=BaseModel)
CreateSchemaType = TypeVar("CreateSchemaType", bound=SQLModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=SQLModel)

class BaseRepository(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    def __init__(self, model: Type[ModelType]):
        self.model = model
    
    def get(self, db: Session, id: UUID) -> Optional[ModelType]:
        return db.get(self.model, id)
    
    def get_multi(
        self, db: Session, *, skip: int = 0, limit: int = 100
    ) -> List[ModelType]:
        statement = select(self.model).offset(skip).limit(limit)
        return db.exec(statement).all()
    
    def create(self, db: Session, *, obj_in: CreateSchemaType) -> ModelType:
       db_obj = self.model.model_validate(obj_in)
       db.add(db_obj)
       db.commit()
       db.refresh(db_obj)
       return db_obj
    
    def update(
        self, db: Session, *, db_obj: ModelType, obj_in: Union[UpdateSchemaType, Dict[str, Any]]
    ) -> ModelType:
        obj_data ={}
        if isinstance(obj_in, dict):
            obj_data = obj_in
        else:
            obj_data = obj_in.model_dump(exclude_unset=True)
        for field, value in obj_data.items():
            if hasattr(db_obj, field):
                setattr(db_obj, field, value)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj
    
    def remove(
        self, db: Session, *, id: UUID
    ) -> Optional[ModelType]:
        obj = db.get(self.model, id)
        if obj:
            db.delete(obj)
            db.commit()
        return obj