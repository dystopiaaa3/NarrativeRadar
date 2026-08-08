from datetime import datetime

from sqlalchemy import (
    ForeignKey,
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


class Alert(Base):
    __tablename__ = "alerts"

    id: Mapped[int] = mapped_column(
        primary_key=True
    )

    coin_id: Mapped[int] = mapped_column(
        ForeignKey("coins.id"),
        index=True
    )

    alert_type: Mapped[str] = mapped_column(
        String(50)
    )

    message: Mapped[str] = mapped_column(
        String(500)
    )

    confidence: Mapped[float] = mapped_column(
        Float,
        default=0.0
    )

    triggered: Mapped[bool] = mapped_column(
        Boolean,
        default=False
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow
    )