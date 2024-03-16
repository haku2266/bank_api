from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.schemas import UserCreateSchema, UserList
from src.auth.utils import hash_password
from src.auth.crud import UserCRUD
from src.database import get_async_session

router = APIRouter(prefix="/user", tags=["User"])


@router.post("/create/")
async def create_user(
    user_schema: UserCreateSchema, db: AsyncSession = Depends(get_async_session)
):
    data = user_schema.model_dump()
    password = data.pop("password")
    data.update({"hashed_password": hash_password(password)})

    result = await UserCRUD.create_user(user_data=data, db=db)

    return {
        "message": "User created successfully. To activate your account, check your gmail.",
        "data": UserList.model_validate(result, from_attributes=True),
    }


@router.get("/list/")
async def list_users(
    db: AsyncSession = Depends(get_async_session),
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1),
):
    result = await UserCRUD.list_users(db=db, page=page, size=size)
    if not result:
        return {
            "page": page,
            "size": size,
            "data": None,
        }
    return {
        "page": page,
        "size": size,
        "data": [
            UserList.model_validate(user, from_attributes=True) for user in result
        ],
    }
