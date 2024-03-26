from datetime import datetime, timedelta
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict, Extra


class LoanTypeCreateSchema(BaseModel):
    name: str = Field(max_length=100, examples=["Educational Loan"])
    interest: int | None = Field(default=0, ge=0)
    days: int = Field(default=5, ge=1)
    bank_id: UUID

    class Config:
        extra = Extra.forbid


class LoanTypesListSchema(BaseModel):
    id: int
    name: str = Field(max_length=100, examples=["Educational Loan"])
    interest: int | None = Field(default=0, ge=0)
    days: int = Field(default=5, ge=1)

    model_config = ConfigDict(from_attributes=True)


class LoanCreateSchema(BaseModel):
    loan_type_id: int = Field(gt=0)
    amount_out: int = Field(gt=100_000, lt=5_000_000)
    expired_at: datetime = Field(examples=[datetime.now() + timedelta(days=5)])

    class Config:
        extra = Extra.forbid


class LoanListSchema(BaseModel):
    id: int
    account_id: int
    loan_type_id: int
    amount_out: int
    amount_expected: float
    expired_at: datetime
    amount_in: int
    is_expired: bool
    is_covered: bool

    class Config:
        extra = Extra.forbid


class LoanCompensationCreateSchema(BaseModel):
    amount: int = Field(gt=0)

    class Config:
        extra = Extra.forbid


class LoanCompensationListSchema(BaseModel):
    id: int
    amount: int = Field(gt=0)
    loan_id: int = Field(gt=0)

    model_config = ConfigDict(from_attributes=True)
