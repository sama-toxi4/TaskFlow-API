from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


class TaskBase(BaseModel):
    title: str = Field(min_length=1, max_length=50)
    description: str = Field(min_length=1, max_length=100)

class TaskCreate(TaskBase):
    title: str = Field(min_length=1, max_length=50)
    description: str = Field(min_length=1, max_length=500)
    status: str = Field(default="todo", pattern="^(todo|in_progress|done)$")
    priority: str = Field(default="medium", pattern="^(low|medium|high)$")
    due_date: datetime | None = None
    assignee_id: int | None = None
    tag_ids: list[int] = []

class TaskUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=50)
    description: str | None = Field(default=None, min_length=1, max_length=500)
    status: str | None = Field(default=None, pattern="^(todo|in_progress|done)$")
    priority: str | None = Field(default=None, pattern="^(low|medium|high)$")
    due_date: datetime | None = None
    assignee_id: int | None = None
    tag_ids: list[int] | None = None

class TaskResponse(BaseModel):
    id: int
    title: str
    description: str
    status: str
    priority: str
    due_date: datetime | None
    project_id: int
    assignee_id: int | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)