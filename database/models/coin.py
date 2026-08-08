from datetime import datetime

from sqlalchemy import (
    String,
    Boolean,
    DateTime,
)

from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship,
)

from ..base import Base


class Coin(Base):

    __tablename__ = "coins"


    id: Mapped[int] = mapped_column(
        primary_key=True
    )


    address: Mapped[str] = mapped_column(
        String(64),
        unique=True,
        index=True
    )


    name: Mapped[str] = mapped_column(
        String(100)
    )


    symbol: Mapped[str] = mapped_column(
        String(25),
        index=True
    )


    chain: Mapped[str] = mapped_column(
        String(20),
        default="solana"
    )


    first_seen: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow
    )


    active: Mapped[bool] = mapped_column(
        Boolean,
        default=True
    )


    market_observations = relationship(
        "MarketObservation",
        back_populates="coin"
    )


    social_observations = relationship(
        "SocialObservation",
        back_populates="coin"
    )


    wallet_activities = relationship(
        "WalletActivity",
        back_populates="coin"
    )


    analyses = relationship(
        "Analysis",
        back_populates="coin"
    )


    radar_results = relationship(
        "RadarResult",
        back_populates="coin"
    )