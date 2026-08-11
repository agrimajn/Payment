"""ORM models — the tables this service persists to disk.

Note what is deliberately absent here: there is no column for a raw
card number. Only a token and its encrypted counterpart are ever
written to the database.
"""

from datetime import datetime, timezone

from sqlalchemy import DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class CardToken(Base):
    """A single tokenized card record."""

    __tablename__ = "card_tokens"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    token: Mapped[str] = mapped_column(String, unique=True, index=True)
    encrypted_card_data: Mapped[str] = mapped_column(String)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )
