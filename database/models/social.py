from datetime import datetime

from sqlalchemy import (
    String,
    Integer,
    Float,
    DateTime,
    ForeignKey
)

from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship
)

from ..base import Base


class SocialObservation(Base):

    __tablename__ = "social_observations"


    id: Mapped[int] = mapped_column(
        primary_key=True
    )


    coin_id: Mapped[int] = mapped_column(
        ForeignKey("coins.id"),
        index=True
    )


    coin_address: Mapped[str] = mapped_column(
        String(100),
        index=True
    )


    mentions: Mapped[int] = mapped_column(
        Integer
    )


    engagement: Mapped[int] = mapped_column(
        Integer
    )


    community_size: Mapped[int] = mapped_column(
        Integer
    )


    growth_rate: Mapped[float] = mapped_column(
        Float
    )


    timestamp: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow
    )


    coin = relationship(
        "Coin",
        back_populates="social_observations"
    )