from datetime import datetime
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


class LoanTypesListSchema(BaseModel):
    id: int
    name: str = Field(max_length=100, examples=["Educational Loan"])
    interest: int | None = Field(default=0, ge=0)
    days: int = Field(default=5, ge=1)

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
