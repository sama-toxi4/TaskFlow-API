from datetime import datetime
from typing import List, Generic, TypeVar
from pydantic import BaseModel, Field, ConfigDict

T = TypeVar('T')


class ProjectBase(BaseModel):
    name: str = Field(min_length=1, max_length=50)
    description: str = Field(min_length=1, max_length=200)

class ProjectCreate(ProjectBase):
    pass

class ProjectUpdate(ProjectBase):
    name: str | None = Field(default=None, min_length=1, max_length=50)
    description: str | None = Field(default=None, min_length=1, max_length=200)

class ProjectResponse(ProjectBase):
    id: int
    owner_id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class PageResponse(BaseModel, Generic[T]):
    items: List[T]
    total: int
    page: int
    per_page: int
    total_pages: int

