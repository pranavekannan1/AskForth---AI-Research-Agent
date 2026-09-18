from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, JSON, String, Text
from sqlalchemy.sql import func
from sqlalchemy.orm import Mapped, mapped_column

from core.database import Base


class ResearchProject(Base):
    __tablename__ = "research_projects"

    id: Mapped[str] = mapped_column(String, primary_key=True, index=True)
    user_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    topic: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String, nullable=False, default="interview")

    question_index: Mapped[int] = mapped_column(nullable=False, default=0)
    current_question: Mapped[str | None] = mapped_column(Text, nullable=True)

    answers: Mapped[list[Any]] = mapped_column(JSON, nullable=False, default=list)
    profile: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)

    research_plan: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    report: Mapped[str | None] = mapped_column(Text, nullable=True)
    sources: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    report_status: Mapped[str] = mapped_column(String, nullable=False, default="not_started")

    # Persistent conversation for the ChatGPT-like research workspace.
    messages: Mapped[list[dict[str, Any]]] = mapped_column(JSON, nullable=False, default=list)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
