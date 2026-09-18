from sqlalchemy import Column, DateTime, String
from sqlalchemy.sql import func

from core.database import Base


class User(Base):
    __tablename__ = "users"

    uid = Column(
        String,
        primary_key=True,
        index=True,
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )