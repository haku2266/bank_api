from datetime import datetime

from fastapi import HTTPException, status
from pydantic import BaseModel, Field, field_validator, EmailStr, ConfigDict, Extra
import re
import phonenumbers


class UserCreateSchema(BaseModel):
    name: str = Field(max_length=100)
    email: EmailStr
    phone_number: str = Field(max_length=13, examples=["+998883010504"])
    password: str = Field(min_length=8)

    class Config:
        extra = Extra.forbid

    @field_validator("phone_number")
    @classmethod
    def validate_phone_number(cls, value):

        # replacing all characters, except digits and '+'
        clean_value = re.sub("[^0-9+]+", "", value)

        if len(clean_value) != 13:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={"phone_number": "phone number must be 13 characters long"},
            )

        # checking if phone number belongs to uzbekistan
        if not clean_value.startswith("+998"):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={"phone_number": "phone number is not local"},
            )

        # checking is phone number is valid
        try:
            z = phonenumbers.parse(clean_value)  # +998990483839
            if not phonenumbers.is_valid_number(z):
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail={"phone_number": "phone number is invalid"},
                )
        except phonenumbers.NumberParseException:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={"phone_number": "phone number is invalid"},
            )
        return clean_value


class UserListSchema(BaseModel):
    id: int
    name: str = Field(max_length=100)
    email: EmailStr
    phone_number: str = Field(max_length=13, examples=["+998883010504"])
    accounts_number: int | None
    is_active: bool
    created_at: datetime | None

    model_config = ConfigDict(from_attributes=True)


class UserPartialUpdateSchema(BaseModel):

    name: str | None = Field(max_length=100, default=None)
    email: EmailStr | None = None
    phone_number: str | None = Field(
        max_length=13, default=None, examples=["+998883010504"]
    )

    class Config:
        extra = Extra.forbid

    @field_validator("phone_number")
    @classmethod
    def validate_phone_number(cls, value):

        # replacing all characters, except digits and '+'
        clean_value = re.sub("[^0-9+]+", "", value)

        if len(clean_value) != 13:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={"phone_number": "phone number must be 13 characters long"},
            )

        # checking if phone number belongs to uzbekistan
        if not clean_value.startswith("+998"):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={"phone_number": "phone number is not local"},
            )

        # checking is phone number is valid
        try:
            z = phonenumbers.parse(clean_value)  # +998990483839
            if not phonenumbers.is_valid_number(z):
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail={"phone_number": "phone number is invalid"},
                )
        except phonenumbers.NumberParseException:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={"phone_number": "phone number is invalid"},
            )
        return clean_value


class TokenInfo(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str | None = "Bearer"
