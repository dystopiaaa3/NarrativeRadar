from sqlalchemy import (
    String,
    Boolean,
)

from sqlalchemy.orm import (
    Mapped,
    mapped_column,
)

from ..base import Base


class Attribute(Base):
    __tablename__ = "attributes"

    id: Mapped[int] = mapped_column(
        primary_key=True
    )

    name: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        index=True
    )

    category: Mapped[str] = mapped_column(
        String(50),
        index=True
    )

    description: Mapped[str] = mapped_column(
        String(255)
    )

    active: Mapped[bool] = mapped_column(
        Boolean,
        default=True
    )