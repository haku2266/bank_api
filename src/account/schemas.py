from datetime import datetime, timedelta
from uuid import UUID
from pydantic import BaseModel, Field, ConfigDict, Extra


class AccountCreateSchema(BaseModel):
    user_id: int = Field(gt=0)
    money: int | None = Field(default=0, ge=0)

    class Config:
        extra = Extra.forbid


class AccountListSchema(BaseModel):
    id: int
    user_id: int = Field(gt=0, examples=[1])
    money: int | None = Field(default=0, ge=0)
    created_at: datetime | None


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
