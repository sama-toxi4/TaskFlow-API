from datetime import datetime
from typing import List
from sqlalchemy import String, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base

class Project(Base):
    __tablename__ = "project"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    description: Mapped[str] = mapped_column(String(100), nullable=False)
    owner_id: Mapped[int] = mapped_column(ForeignKey("user.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now(), onupdate=func.now(), nullable=False)

    owner: Mapped["User"] = relationship(back_populates="owned_projects")
    task: Mapped[List["Task"]] = relationship(back_populates="project")

    members: Mapped[list["User"]] = relationship(secondary="project_users",back_populates="projects")

