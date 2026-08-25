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

class TaskUpdate(TaskBase):
    title: str | None = Field(default=None, min_length=1, max_length=50)
    description: str | None = Field(default=None, min_length=1, max_length=500)
    status: str | None = Field(default="todo", pattern="^(todo|in_progress|done)$")
    priority: str | None = Field(default="medium", pattern="^(low|medium|high)$")

class TaskResponse(TaskBase):
    id: int

    model_config = ConfigDict(from_attributes=True)