from datetime import datetime, timezone
from typing import Annotated

from sqlalchemy import String, Text, ForeignKey, text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.account.models import Account
from src.database import Base
from uuid import uuid4, UUID
from typing_extensions import TYPE_CHECKING


if TYPE_CHECKING:
    from src.auth.models import User
    from src.teller.models import Teller
    from src.loan.models import LoanType

created_at = Annotated[
    datetime,
    mapped_column(
        default=datetime.now(), server_default=text("TIMEZONE('utc', now())")
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


class Bank(Base):
    __tablename__ = "bank"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(String(100), unique=True)
    location: Mapped[str | None] = mapped_column(Text, nullable=True)

    users: Mapped[list["User"]] = relationship(
        secondary="bank_user_association", back_populates="banks"
    )
    tellers: Mapped[list["Teller"]] = relationship(back_populates="bank")
    accounts: Mapped[list["Account"]] = relationship(back_populates="bank")
    loan_types: Mapped[list["LoanType"]] = relationship(back_populates="bank")

    def __repr__(self) -> str:
        return f"<Bank: {self.name}>"


class BankUserAssociation(Base):
    __tablename__ = "bank_user_association"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"))
    bank_id: Mapped[int] = mapped_column(ForeignKey("bank.id"))

    __table_args__ = (
        UniqueConstraint("user_id", "bank_id", name="unique_user_bank_combination"),
    )

    def __repr__(self) -> str:
        return f"<BankUserAssociation: {self.id}"


