from fastapi import Path, Depends, HTTPException, status
from typing import Annotated
from sqlalchemy.ext.asyncio import AsyncSession

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
