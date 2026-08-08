from sqlalchemy import ForeignKey

from sqlalchemy.orm import (
    Mapped,
    mapped_column,
)

from ..base import Base


class CoinAttribute(Base):
    __tablename__ = "coin_attributes"

    id: Mapped[int] = mapped_column(
        primary_key=True
    )

    coin_id: Mapped[int] = mapped_column(
        ForeignKey("coins.id"),
        index=True
    )

    attribute_id: Mapped[int] = mapped_column(
        ForeignKey("attributes.id"),
        index=True
    )

    confidence: Mapped[float] = mapped_column(
        default=0.0
    )