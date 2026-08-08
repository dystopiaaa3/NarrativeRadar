from datetime import datetime

from sqlalchemy import (
    String,
    Float,
    Boolean,
    DateTime,
)

from sqlalchemy.orm import (
    Mapped,
    mapped_column,
)

from ..base import Base


class CaseStudy(Base):
    __tablename__ = "case_studies"

    id: Mapped[int] = mapped_column(
        primary_key=True
    )

    name: Mapped[str] = mapped_column(
        String(100)
    )

    symbol: Mapped[str] = mapped_column(
        String(25)
    )

    category: Mapped[str] = mapped_column(
        String(30)
    )

    outcome: Mapped[str] = mapped_column(
        String(50)
    )

    peak_multiplier: Mapped[float] = mapped_column(
        Float
    )

    success: Mapped[bool] = mapped_column(
        Boolean
    )

    explanation: Mapped[str] = mapped_column(
        String(500)
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow
    )