from typing import List

from sqlalchemy import String, ForeignKey, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class User(Base):
    __tablename__ = "user"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(60), nullable=False)
    role: Mapped[str] = mapped_column(Enum("admin", "user", native_enum=False), default="user", nullable=False)
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)

    owned_projects: Mapped[List["Project"]] = relationship(back_populates="owner")
    assigned_tasks: Mapped[List["Task"]] = relationship(back_populates="assignee")

    projects: Mapped[list["Project"]] = relationship(secondary="project_users",back_populates="members")


class ProjectUsers(Base):
    __tablename__ = "project_users"

    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"), primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("project.id"), primary_key=True)