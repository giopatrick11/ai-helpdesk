from sqlalchemy import String, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from app.database.database import Base


class Ticket(Base):
    __tablename__ = "tickets"

    id: Mapped[int] = mapped_column(primary_key=True)

    user_id: Mapped[int] = mapped_column(
    ForeignKey("users.id")
    )

    subject: Mapped[str] = mapped_column(
        String(255)
    )

    description: Mapped[str] = mapped_column(
        Text
    )

    priority: Mapped[str] = mapped_column(
        String(50)
    )

    status: Mapped[str] = mapped_column(
        String(50),
        default="open"
    )

    category: Mapped[str | None] = mapped_column(
    String(100),
    nullable=True
)

    ai_summary: Mapped[str | None] = mapped_column(
    Text,
    nullable=True
    )
    