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


class Analysis(Base):

    __tablename__ = "analyses"


    id: Mapped[int] = mapped_column(
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


    signal_count: Mapped[int] = mapped_column(
        Integer
    )


    timestamp: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        index=True
    )


    coin = relationship(
        "Coin",
        back_populates="analyses"
    )