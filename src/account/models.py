from datetime import datetime, timezone
from typing import Annotated

from sqlalchemy import ForeignKey, CheckConstraint, text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from src.database import Base
from typing_extensions import TYPE_CHECKING

if TYPE_CHECKING:
    from src.auth.models import User
    from src.bank.models import Bank
    from src.loan.models import Loan


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


class Deposit(Base):
    __tablename__ = "deposit"
    id: Mapped[int] = mapped_column(primary_key=True)
    amount: Mapped[int] = mapped_column(nullable=False)
    account_id: Mapped[int] = mapped_column(
        ForeignKey("account.id", ondelete="CASCADE")
    )
    created_at: Mapped[created_at]
    account: Mapped["Account"] = relationship(back_populates="deposits")

    def __repr__(self) -> str:
        return f"<Deposit:{self.id}~Account:{self.account_id}"

    __table_args__ = (
        CheckConstraint(
            "amount > 100000",
            name="check_d_amount_gt_100k",
        ),
    )


class Withdraw(Base):
    __tablename__ = "withdraw"
    id: Mapped[int] = mapped_column(primary_key=True)
    amount: Mapped[int] = mapped_column(nullable=False)
    account_id: Mapped[int] = mapped_column(
        ForeignKey("account.id", ondelete="CASCADE")
    )
    created_at: Mapped[created_at]

    account: Mapped["Account"] = relationship(back_populates="withdraws")

    def __repr__(self) -> str:
        return f"<Withdraw:{self.id}~Account:{self.account_id}"

    __table_args__ = (
        CheckConstraint(
            "amount BETWEEN 100000 AND 3000000",
            name="check_w_amount_between_range",
        ),
    )


class Account(Base):
    __tablename__ = "account"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id", ondelete="CASCADE"))
    bank_id: Mapped[int] = mapped_column(ForeignKey("bank.id", ondelete="CASCADE"))
    money: Mapped[int | None] = mapped_column(default=0)
    created_at: Mapped[created_at]

    user: Mapped["User"] = relationship(back_populates="accounts")
    bank: Mapped["Bank"] = relationship(back_populates="accounts")
    deposits: Mapped[list["Deposit"]] = relationship(back_populates="account")
    withdraws: Mapped[list["Withdraw"]] = relationship(back_populates="account")
    loans: Mapped[list["Loan"]] = relationship(back_populates="account")

    __table_args__ = (
        UniqueConstraint("user_id", "bank_id", name="unique_account_in_bank"),
    )

    def __repr__(self) -> str:
        return f"<Account:{self.id}~Bank:{self.bank_id}>"
