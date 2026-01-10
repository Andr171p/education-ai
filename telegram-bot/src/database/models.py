from typing import Any

from datetime import datetime
from uuid import UUID

from sqlalchemy import JSON, BigInteger, DateTime, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base


class Task(Base):
    __tablename__ = "tasks"

    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[str]
    resource_id: Mapped[UUID]


class Attachment(Base):
    __tablename__ = "attachments"

    original_filename: Mapped[str]
    filepath: Mapped[str] = mapped_column(unique=True)
    mime_type: Mapped[str]
    size: Mapped[int]
    uploaded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class Course(Base):
    __tablename__ = "courses"

    title: Mapped[str]
    description: Mapped[str] = mapped_column(Text)
    discipline: Mapped[str]
    creator_id: Mapped[int] = mapped_column(BigInteger)

    modules: Mapped[list["Module"]] = relationship(back_populates="course")


class Module(Base):
    __tablename__ = "modules"

    course_id: Mapped[UUID] = mapped_column(ForeignKey("courses.id"), unique=False)
    title: Mapped[str]
    description: Mapped[str] = mapped_column(Text)
    order: Mapped[int]
    content_blocks: Mapped[dict[str, Any]] = mapped_column(JSON)
    dependencies: Mapped[list[UUID]] = mapped_column(JSON)

    course: Mapped["Course"] = relationship(back_populates="modules")
    assessments: Mapped[list["Assessment"]] = relationship(back_populates="module")


class Assessment(Base):
    __tablename__ = "assessments"

    module_id: Mapped[UUID] = mapped_column(ForeignKey("modules.id"), unique=False)
    assessment_type: Mapped[str]
    title: Mapped[str]
    description: Mapped[str] = mapped_column(Text)
    verification_rules: Mapped[dict[str, Any]] = mapped_column(JSON)

    module: Mapped["Module"] = relationship(back_populates="assessments")
