from fastapi import Path, Depends, HTTPException, status, Form
from fastapi.security import HTTPAuthorizationCredentials
from typing import Annotated
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.auth.utils import validate_password, decode_jwt
from src.database import get_async_session
from src.auth.models import User
from src.auth.crud import UserCRUD


async def retrieve_user_dependency(
    user_id: Annotated[int, Path(gt=0)],
    db: AsyncSession = Depends(get_async_session),
) -> User:
    result = await UserCRUD.retrieve_user(db=db, user_id=user_id)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"id": f"User with id {user_id} is not found"},
        )
    return result


async def validate_user(
    phone_number: str = Form(),
    password: str = Form(),
    db: AsyncSession = Depends(get_async_session),
):

    query = select(User).where(User.phone_number == phone_number)

    user = await db.scalar(query)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="invalid phone number. User with phone number does not exist",
        )

    else:

        if not validate_password(password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="incorrect password",
            )

        # if not user.is_active:
        #     raise HTTPException(status_code=403, detail="user inactive")

        return user

