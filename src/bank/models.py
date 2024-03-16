from datetime import datetime, timezone
from typing import Annotated

from sqlalchemy import String, Text, ForeignKey, CheckConstraint, text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from src.database import Base
from uuid import uuid4, UUID
from typing_extensions import TYPE_CHECKING

if TYPE_CHECKING:
    from src.auth.models import User

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

    def __repr__(self) -> str:
        return f"<BankUserAssociation: {self.id}"


class Teller(Base):
    __tablename__ = "teller"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    bank_id: Mapped[int] = mapped_column(ForeignKey("bank.id", ondelete="CASCADE"))

    bank: Mapped["Bank"] = relationship(back_populates="tellers")

    def __repr__(self) -> str:
        return f"<Teller:{self.id}~Bank:{self.bank_id}>"


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

    user: Mapped['User'] = relationship(back_populates="accounts")
    bank: Mapped['Bank'] = relationship(back_populates="accounts")
    deposits: Mapped[list["Deposit"]] = relationship(back_populates="account")
    withdraws: Mapped[list["Withdraw"]] = relationship(back_populates="account")
    loans: Mapped[list["Loan"]] = relationship(back_populates="account")

    def __repr__(self) -> str:
        return f"<Account:{self.id}~Bank:{self.bank_id}>"


class LoanType(Base):
    __tablename__ = "loan_type"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True)
    interest: Mapped[int | None] = mapped_column(default=0)
    days: Mapped[int] = mapped_column(default=5)
    bank_id: Mapped[int] = mapped_column(ForeignKey("bank.id", ondelete="CASCADE"))
    created_at: Mapped[created_at]

    bank: Mapped["Bank"] = relationship(back_populates="loan_types")

    __table_args__ = (
        CheckConstraint(
            "interest >= 0",
            name="check_interest_gt_0",
        ),
        CheckConstraint(
            "days >= 1",
            name="check_days_gt_1",
        ),
    )

    def __repr__(self) -> str:
        return f"<LoanType:{self.id}~Bank:{self.bank_id}"


class Loan(Base):
    __tablename__ = "loan"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"))
    account_id: Mapped[int] = mapped_column(
        ForeignKey("account.id", ondelete="RESTRICT")
    )
    amount_out: Mapped[int]
    amount_in: Mapped[int | None] = mapped_column(default=0)

    loan_type: Mapped["LoanType"] = mapped_column(
        ForeignKey("loan_type.id", ondelete="RESTRICT")
    )
    is_expired: Mapped[bool | None] = mapped_column(default=False)
    created_at: Mapped[created_at]
    expired_at: Mapped[datetime]

    compensations: Mapped[list["LoanCompensation"] | None] = relationship(
        back_populates="loan"
    )
    user: Mapped["User"] = relationship(back_populates="loans")
    account: Mapped["Account"] = relationship(back_populates="loans")

    __table_args__ = (
        CheckConstraint(
            "amount_out BETWEEN 100000 AND 5000000",
            name="check_amount_out_between_range",
        ),
        CheckConstraint("amount_in > 0", name="check_amount_in_positive"),
    )

    def __repr__(self) -> str:
        return f"<Loan:{self.id}~Acc{self.account_id}>"


class LoanCompensation(Base):
    __tablename__ = "loan_compensation"
    id: Mapped[int] = mapped_column(primary_key=True)
    amount: Mapped[int] = mapped_column(nullable=False)
    loan_id: Mapped[int] = mapped_column(ForeignKey("loan.id", ondelete="RESTRICT"))
    created_at: Mapped[created_at]

    loan: Mapped["Loan"] = relationship(back_populates="compensations")

    __table_args__ = (
        CheckConstraint(
            "amount > 100000",
            name="check_d_amount_gt_100k",
        ),
    )

    def __repr__(self) -> str:
        return f"<LoanCompensation:{self.id}"
