from datetime import datetime

from sqlalchemy import (
    String,
    Float,
    Integer,
    DateTime,
    Boolean,
)

from sqlalchemy.orm import (
    Mapped,
    mapped_column,
)

from ..base import Base


class Pattern(Base):
    __tablename__ = "patterns"

    id: Mapped[int] = mapped_column(
        primary_key=True
    )

    name: Mapped[str] = mapped_column(
        String(100),
        index=True
    )

    description: Mapped[str] = mapped_column(
        String(500)
    )

    occurrences: Mapped[int] = mapped_column(
        Integer,
        default=0
    )

    success_rate: Mapped[float] = mapped_column(
        Float,
        default=0.0
    )

    average_return: Mapped[float] = mapped_column(
        Float,
        default=0.0
    )

    active: Mapped[bool] = mapped_column(
        Boolean,
        default=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow
    )