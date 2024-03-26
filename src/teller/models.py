from datetime import datetime, timezone
from typing import Annotated

from sqlalchemy import ForeignKey, text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from src.database import Base
from typing_extensions import TYPE_CHECKING

if TYPE_CHECKING:
    from src.auth.models import User
    from src.bank.models import Bank

created_at = Annotated[
    datetime, mapped_column(server_default=text("TIMEZONE('utc', now())"))
]
updated_at = Annotated[
    datetime,
    mapped_column(
        server_default=text("TIMEZONE('utc', now())"),
        onupdate=datetime.now(tz=timezone.utc),
    ),
]


class Teller(Base):
    __tablename__ = "teller"
    id: Mapped[int] = mapped_column(primary_key=True)
    bank_id: Mapped[int] = mapped_column(ForeignKey("bank.id"))
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"), unique=True)

    bank: Mapped["Bank"] = relationship(back_populates="tellers")
    user: Mapped["User"] = relationship(back_populates="teller")

    def __repr__(self):
        return f"<Teller:{self.id}>"
