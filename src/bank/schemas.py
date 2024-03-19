from datetime import datetime, timedelta
from uuid import UUID

from fastapi import HTTPException, status
from pydantic import BaseModel, Field, field_validator, EmailStr, ConfigDict, Extra
import re
import phonenumbers

from src.auth.schemas import UserListSchema


class BankCreateSchema(BaseModel):
    name: str = Field(max_length=100, examples=["Super Bank"])
    location: str | None = Field(
        examples=["San Francisco Ave, St. Louisiana, 12th Block"]
    )

    class Config:
        extra = Extra.forbid


class BankCreatedRetrieve(BaseModel):
    id: UUID
    name: str = Field(max_length=100, examples=["Super Bank"])
    location: str | None = Field(
        examples=["San Francisco Ave, St. Louisiana, 12th Block"]
    )

    model_config = ConfigDict(from_attributes=True)


class BankListSchema(BaseModel):
    id: UUID
    name: str = Field(max_length=100, examples=["Super Bank"])
    location: str | None = Field(
        examples=["San Francisco Ave, St. Louisiana, 12th Block"]
    )
    loan_types: list["LoanTypesListSchema"] | None = []

    model_config = ConfigDict(from_attributes=True)


class BankPartialUpdateSchema(BaseModel):
    name: str | None = Field(default=None, max_length=100, examples=["Super Bank"])
    location: str | None = Field(
        examples=["San Francisco Ave, St. Louisiana, 12th Block"],
        default=None,
    )

    class Config:
        extra = Extra.forbid


class AccountCreateSchema(BaseModel):
    user_id: int = Field(gt=0, examples=[1])
    bank_id: UUID
    money: int | None = Field(default=0, ge=0)

    class Config:
        extra = Extra.forbid


class AccountListSchema(BaseModel):
    id: int
    user_id: int = Field(gt=0, examples=[1])
    money: int | None = Field(default=0, ge=0)
    created_at: datetime | None


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


class DepositCreateSchema(BaseModel):
    amount: int = Field(gt=100_000)

    class Config:
        extra = Extra.forbid


class DepositCreatedListSchema(BaseModel):
    id: int
    amount: int
    account_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class WithdrawCreateSchema(BaseModel):
    amount: int = Field(gt=100_000, lt=3_000_000)

    class Config:
        extra = Extra.forbid


class WithdrawCreatedListSchema(BaseModel):
    id: int
    amount: int
    account_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
