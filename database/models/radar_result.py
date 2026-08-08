from datetime import datetime

from sqlalchemy import (
    Integer,
    Float,
    String,
    DateTime,
    ForeignKey,
)

from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship,
)

from ..base import Base


class RadarResult(Base):

    __tablename__ = "radar_results"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True
    )

    coin_id: Mapped[int] = mapped_column(
        ForeignKey("coins.id"),
        index=True
    )

    market_score: Mapped[float] = mapped_column(
        Float
    )

    social_score: Mapped[float] = mapped_column(
        Float
    )

    wallet_score: Mapped[float] = mapped_column(
        Float
    )

    combined_score: Mapped[float] = mapped_column(
        Float
    )

    narrative: Mapped[str] = mapped_column(
        String(100)
    )

    signal: Mapped[str] = mapped_column(
        String(100)
    )

    confidence: Mapped[float] = mapped_column(
        Float
    )

    decision: Mapped[str] = mapped_column(
        String(100)
    )

    risk: Mapped[str] = mapped_column(
        String(50)
    )

    timestamp: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        index=True
    )

    coin = relationship(
        "Coin",
        back_populates="radar_results"
    )
