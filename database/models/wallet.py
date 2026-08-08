from datetime import datetime

from sqlalchemy import (
    String,
    Boolean,
    DateTime,
    Float,
)

from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship,
)

from ..base import Base


class Wallet(Base):

    __tablename__ = "wallets"


    id: Mapped[int] = mapped_column(
        primary_key=True
    )


    address: Mapped[str] = mapped_column(
        String(64),
        unique=True,
        index=True
    )


    label: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True
    )


    is_smart_wallet: Mapped[bool] = mapped_column(
        Boolean,
        default=False
    )


    success_rate: Mapped[float] = mapped_column(
        Float,
        default=0.0
    )


    average_roi: Mapped[float] = mapped_column(
        Float,
        default=0.0
    )


    first_seen: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow
    )


    active: Mapped[bool] = mapped_column(
        Boolean,
        default=True
    )


    # =========================
    # Relationships
    # =========================

    activities = relationship(
        "WalletActivity",
        back_populates="wallet"
    )