from sqlalchemy import (
    ForeignKey,
)

from sqlalchemy.orm import (
    Mapped,
    mapped_column,
)

from ..base import Base


class CoinNarrative(Base):
    __tablename__ = "coin_narratives"

    id: Mapped[int] = mapped_column(
        primary_key=True
    )

    coin_id: Mapped[int] = mapped_column(
        ForeignKey("coins.id"),
        index=True
    )

    narrative_id: Mapped[int] = mapped_column(
        ForeignKey("narratives.id"),
        index=True
    )

    confidence: Mapped[float] = mapped_column(
        default=0.0
    )