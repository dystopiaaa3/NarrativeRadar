from datetime import datetime

from sqlalchemy import (
    ForeignKey,
    Float,
    String,
    DateTime
)

from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship
)

from ..base import Base


class WalletActivity(Base):

    __tablename__ = "wallet_activities"


    id: Mapped[int] = mapped_column(
        primary_key=True
    )


    wallet_id: Mapped[int] = mapped_column(
        ForeignKey("wallets.id"),
        index=True
    )


    coin_id: Mapped[int] = mapped_column(
        ForeignKey("coins.id"),
        index=True
    )


    action: Mapped[str] = mapped_column(
        String(20)
    )


    amount_sol: Mapped[float] = mapped_column(
        Float
    )


    token_amount: Mapped[float] = mapped_column(
        Float,
        default=0
    )


    market_cap_at_time: Mapped[float] = mapped_column(
        Float
    )


    timestamp: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        index=True
    )


    # =========================
    # Relationships
    # =========================

    coin = relationship(
        "Coin",
        back_populates="wallet_activities"
    )


    wallet = relationship(
        "Wallet",
        back_populates="activities"
    )