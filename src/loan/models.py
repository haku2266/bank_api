from datetime import datetime, timezone
from typing import Annotated

from sqlalchemy import String, ForeignKey, CheckConstraint, text
from sqlalchemy.orm import Mapped, mapped_column, relationship


from src.database import Base
from typing_extensions import TYPE_CHECKING

if TYPE_CHECKING:
    from src.account.models import Account
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


class LoanType(Base):
    __tablename__ = "loan_type"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True)
    interest: Mapped[int | None] = mapped_column(default=0)
    days: Mapped[int] = mapped_column(default=5)
    bank_id: Mapped[int] = mapped_column(ForeignKey("bank.id", ondelete="CASCADE"))
    created_at: Mapped[created_at]

    bank: Mapped["Bank"] = relationship(back_populates="loan_types")
    loans: Mapped[list["Loan"]] = relationship(back_populates="loan_type")

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
    account_id: Mapped[int] = mapped_column(
        ForeignKey("account.id", ondelete="RESTRICT")
    )
    loan_type_id: Mapped[int] = mapped_column(
        ForeignKey("loan_type.id", ondelete="RESTRICT")
    )

    amount_out: Mapped[int]
    amount_in: Mapped[int | None] = mapped_column(default=0)
    amount_expected: Mapped[float | None] = mapped_column(default=None)

    is_covered: Mapped[bool | None] = mapped_column(default=False)
    is_expired: Mapped[bool | None] = mapped_column(default=False)
    created_at: Mapped[created_at]
    expired_at: Mapped[datetime]

    compensations: Mapped[list["LoanCompensation"] | None] = relationship(
        back_populates="loan"
    )
    account: Mapped["Account"] = relationship(back_populates="loans")
    loan_type: Mapped["LoanType"] = relationship(back_populates="loans")

    __table_args__ = (
        CheckConstraint(
            "amount_out BETWEEN 100000 AND 5000000",
            name="check_amount_out_between_range",
        ),
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
            "amount > 0",
            name="check_d_amount_gt_0",
        ),
    )

    def __repr__(self) -> str:
        return f"<LoanCompensation:{self.id}"
