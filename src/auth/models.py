from typing import Annotated
from typing_extensions import TYPE_CHECKING
from sqlalchemy import String, UniqueConstraint, Text, text, Boolean, LargeBinary
from datetime import datetime, timezone
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database import Base

if TYPE_CHECKING:
    from src.bank.models import Bank, Account, Loan


created_at = Annotated[
    datetime,
    mapped_column(
        default=datetime.now(),
        server_default=text("TIMEZONE('utc', now())"),
    ),
]
updated_at = Annotated[
    datetime,
    mapped_column(
        default=datetime.now(),
        server_default=text("TIMEZONE('utc', now())"),
        onupdate=datetime.now(),
    ),
]


class User(Base):
    __tablename__ = "user"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(nullable=False)
    phone_number: Mapped[str] = mapped_column(String(13), nullable=False)
    hashed_password: Mapped[str] = mapped_column(LargeBinary)
    accounts_number: Mapped[int | None] = mapped_column(default=0, nullable=True)
    is_active: Mapped[bool | None] = mapped_column(
        Boolean, default=False, server_default="false"
    )
    created_at: Mapped[created_at]
    updated_at: Mapped[updated_at]

    banks: Mapped[list["Bank"]] = relationship(
        secondary="bank_user_association",
        back_populates="users",
    )
    accounts: Mapped[list["Account"]] = relationship(back_populates="user")
    loans: Mapped[list["Loan"]] = relationship(back_populates="user")

    __table_args__ = (
        UniqueConstraint(
            "phone_number",
            name="phone_number_unique",
        ),
    )

    def __repr__(self) -> str:
        return f"<User:{self.id}>"
