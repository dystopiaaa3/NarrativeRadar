from datetime import datetime

from sqlalchemy import (
    ForeignKey,
    Float,
    String,
    DateTime,
)

from sqlalchemy.orm import (
    Mapped,
    mapped_column,
)

from ..base import Base


class CoinSimilarity(Base):
    __tablename__ = "coin_similarities"

    id: Mapped[int] = mapped_column(
        primary_key=True
    )

    coin_id: Mapped[int] = mapped_column(
        ForeignKey("coins.id"),
        index=True
    )

    compared_coin_id: Mapped[int] = mapped_column(
        ForeignKey("coins.id"),
        index=True
    )

    similarity_score: Mapped[float] = mapped_column(
        Float
    )

    reason: Mapped[str] = mapped_column(
        String(255)
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow
    )