from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.models import User
from src.auth.schemas import UserCreateSchema, UserListSchema, UserPartialUpdateSchema
from src.auth.utils import hash_password
from src.auth.crud import UserCRUD
from src.database import get_async_session
from src.auth.dependencies import retrieve_user_dependency

router = APIRouter(prefix="/user")


@router.post("/create/", status_code=201, tags=["User"])
async def create_user(
    user_schema: UserCreateSchema, db: AsyncSession = Depends(get_async_session)
):
    data = user_schema.model_dump()
    password = data.pop("password")
    data.update({"hashed_password": hash_password(password)})

    result = await UserCRUD.create_user(user_data=data, db=db)

    return {
        "message": "User created successfully. To activate your account, check your gmail.",
        "data": UserListSchema.model_validate(result, from_attributes=True),
    }


@router.get("/list/", tags=["User"])
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
            UserListSchema.model_validate(user, from_attributes=True) for user in result
        ],
    }


@router.get("/retrieve/{user_id}/", tags=["User"])
async def retrieve_user(user: User = Depends(retrieve_user_dependency)):
    return {
        "data": UserListSchema.model_validate(user, from_attributes=True),
    }


@router.patch("/update/{user_id}/", tags=["User"])
async def partial_update_user(
    user_schema: UserPartialUpdateSchema,
    db: AsyncSession = Depends(get_async_session),
    user: User = Depends(retrieve_user_dependency),
):
    result = await UserCRUD.partial_update_user(
        db=db, user_schema=user_schema, user=user
    )
    return {"data": UserListSchema.model_validate(result, from_attributes=True)}


@router.delete("/delete/{user_id}/", status_code=status.HTTP_204_NO_CONTENT, tags=["User"])
async def delete_user(
    user: User = Depends(retrieve_user_dependency),
    db: AsyncSession = Depends(get_async_session),
):
    result = await UserCRUD.delete_user(db=db, user=user)
    return None


@router.get("/me/", tags=["User-Me"])
async def retrieve_user_me(db: AsyncSession = Depends(get_async_session)):
    pass


@router.get("/me/banks/", tags=["User-Me"])
async def retrieve_my_banks():
    pass


@router.get("/me/accounts/", tags=["User-Me"])
async def retrieve_my_accounts():
    pass


@router.get("/me/loans/", tags=["User-Me"])
async def retrieve_my_loans():
    pass

@router.patch("/me/update/", tags=["User-Me"])
async def update_user_me():
    pass

@router.delete("/me/delete/", tags=["User-Me"])
async def delete_user_me():
    pass