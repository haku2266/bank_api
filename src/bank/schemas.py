from uuid import UUID

from pydantic import BaseModel, Field,  ConfigDict, Extra

from src.loan.schemas import LoanTypesListSchema


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
