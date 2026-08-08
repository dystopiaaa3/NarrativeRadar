from datetime import datetime

from sqlalchemy import (
    Integer,
    Float,
    DateTime,
    ForeignKey,
)

from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship,
)

from ..base import Base


class MarketObservation(Base):

    __tablename__ = "market_observations"


    id: Mapped[int] = mapped_column(
        primary_key=True
    )


    coin_id: Mapped[int] = mapped_column(
        ForeignKey("coins.id"),
        index=True
    )


    price: Mapped[float] = mapped_column(
        Float
    )


    market_cap: Mapped[float] = mapped_column(
        Float
    )


    liquidity: Mapped[float] = mapped_column(
        Float
    )


    volume_24h: Mapped[float] = mapped_column(
        Float
    )


    holders: Mapped[int] = mapped_column(
        Integer
    )


    timestamp: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow
    )


    coin = relationship(
        "Coin",
        back_populates="market_observations"
    )