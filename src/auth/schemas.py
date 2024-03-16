from datetime import datetime

from fastapi import HTTPException, status
from pydantic import BaseModel, Field, field_validator, EmailStr, ConfigDict
import re
import phonenumbers


class UserCreateSchema(BaseModel):
    name: str = Field(max_length=100)
    email: EmailStr
    phone_number: str = Field(max_length=13, examples=["+998883010504"])
    password: str = Field(min_length=8)

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
                    detail={"phone_number", "phone number is invalid"},
                )
        except phonenumbers.NumberParseException:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={"phone_number", "phone number is invalid"},
            )
        return clean_value


class UserList(BaseModel):
    id: int
    name: str = Field(max_length=100)
    email: EmailStr
    phone_number: str = Field(max_length=13, examples=["+998883010504"])
    accounts_number: int | None
    is_active: bool
    created_at: datetime | None

    model_config = ConfigDict(from_attributes=True)
