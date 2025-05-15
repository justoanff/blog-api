from datetime import datetime
from sqlmodel import SQLModel, Field
from sqlalchemy import func
from uuid import UUID, uuid4
class BaseModel (SQLModel):
    id: UUID = Field(default_factory=uuid4, primary_key=True, nullable=False, index=True)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(
        default_factory=datetime.now,
        sa_column_kwargs= {"onupdate": func.now()}
    )