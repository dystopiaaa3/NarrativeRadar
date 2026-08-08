from datetime import datetime

from sqlalchemy import (
    ForeignKey,
    String,
    Float,
    DateTime,
)

from sqlalchemy.orm import (
    Mapped,
    mapped_column,
)

from ..base import Base


class FeedOutcome(Base):

    __tablename__ = "feed_outcomes"

    id: Mapped[int] = mapped_column(
        primary_key=True
    )

    feed_case_id: Mapped[int] = mapped_column(
        ForeignKey("feed_cases.id"),
        index=True
    )

    checkpoint: Mapped[str] = mapped_column(
        String(20),
        index=True
    )

    price: Mapped[float] = mapped_column(
        Float,
        default=0.0
    )

    market_cap: Mapped[float] = mapped_column(
        Float,
        default=0.0
    )

    liquidity: Mapped[float] = mapped_column(
        Float,
        default=0.0
    )

    volume_24h: Mapped[float] = mapped_column(
        Float,
        default=0.0
    )

    return_pct: Mapped[float] = mapped_column(
        Float,
        default=0.0
    )

    liquidity_change_pct: Mapped[float] = mapped_column(
        Float,
        default=0.0
    )

    volume_change_pct: Mapped[float] = mapped_column(
        Float,
        default=0.0
    )

    checked_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow
    )