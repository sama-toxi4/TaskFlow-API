from typing import List
from datetime import datetime
from sqlalchemy import String, ForeignKey, Enum, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base


class Task(Base):
    __tablename__ = "task"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(50), nullable=False)
    description: Mapped[str] = mapped_column(String(100), nullable=False)
    status: Mapped[str] = mapped_column(Enum("todo", "in_progress", "done", native_enum=False), default="todo", nullable=False)
    priority: Mapped[str] = mapped_column(Enum("low", "medium", "high", native_enum=False), default="low", nullable=False)
    due_date: Mapped[datetime] = mapped_column(nullable=False)
    project_id: Mapped[int] = mapped_column(ForeignKey("project.id"), nullable=False)
    assignee_id: Mapped[int] = mapped_column(ForeignKey("user.id"))
    created_at: Mapped[datetime] = mapped_column(nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(nullable=False, server_default=func.now(), onupdate=func.now())

    assignee: Mapped["User"] = relationship(back_populates="assigned_tasks")
    project: Mapped["Project"] = relationship(back_populates="task")

    tags: Mapped[List["Tag"]] = relationship(secondary="task_tags", back_populates="tasks")


class TaskTags(Base):
    __tablename__ = "task_tags"

    task_id: Mapped[int] = mapped_column(ForeignKey("task.id"), primary_key=True)
    tag_id: Mapped[int] = mapped_column(ForeignKey("tag.id"), primary_key=True)