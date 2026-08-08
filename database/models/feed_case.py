from datetime import datetime

from sqlalchemy import (
    ForeignKey,
    String,
    Float,
    Integer,
    DateTime,
)

from sqlalchemy.orm import (
    Mapped,
    mapped_column,
)

from ..base import Base


class FeedCase(Base):

    __tablename__ = "feed_cases"

    id: Mapped[int] = mapped_column(
        primary_key=True
    )

    coin_id: Mapped[int] = mapped_column(
        ForeignKey("coins.id"),
        index=True
    )

    coin_address: Mapped[str] = mapped_column(
        String(64),
        index=True
    )

    name: Mapped[str] = mapped_column(
        String(100),
        default="Unknown"
    )

    symbol: Mapped[str] = mapped_column(
        String(25),
        default="UNKNOWN"
    )

    narrative: Mapped[str] = mapped_column(
        String(100),
        default="UNKNOWN"
    )

    t0_price: Mapped[float] = mapped_column(
        Float,
        default=0.0
    )

    t0_market_cap: Mapped[float] = mapped_column(
        Float,
        default=0.0
    )

    t0_liquidity: Mapped[float] = mapped_column(
        Float,
        default=0.0
    )

    t0_volume_24h: Mapped[float] = mapped_column(
        Float,
        default=0.0
    )

    market_score: Mapped[float] = mapped_column(
        Float,
        default=0.0
    )

    social_score: Mapped[float] = mapped_column(
        Float,
        default=0.0
    )

    wallet_score: Mapped[float] = mapped_column(
        Float,
        default=0.0
    )

    combined_score: Mapped[float] = mapped_column(
        Float,
        default=0.0
    )

    data_quality: Mapped[float] = mapped_column(
        Float,
        default=0.0
    )

    signal: Mapped[str] = mapped_column(
        String(50),
        default="UNKNOWN"
    )

    confidence: Mapped[int] = mapped_column(
        Integer,
        default=0
    )

    decision: Mapped[str] = mapped_column(
        String(50),
        default="UNKNOWN"
    )

    risk: Mapped[str] = mapped_column(
        String(50),
        default="UNKNOWN"
    )

    status: Mapped[str] = mapped_column(
        String(30),
        default="TRACKING",
        index=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        index=True
    )

    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True
    )