from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from src.auth.models import User
from src.database import get_async_session

from src.bank.schemas import (
    BankCreateSchema,
    BankCreatedRetrieve,
    BankListSchema,
    BankPartialUpdateSchema,
)
from src.bank.crud import BankCRUD
from src.bank.models import Bank
from src.bank.dependencies import retrieve_bank_with_users_dependency, retrieve_bank_dependency
from src.auth.dependencies import retrieve_user_dependency

router = APIRouter(prefix="/bank")


@router.post("/create/", response_model=BankCreatedRetrieve, tags=["Bank"])
async def create_bank(
    bank_schema: BankCreateSchema, db: AsyncSession = Depends(get_async_session)
):
    result = await BankCRUD.create_bank(db=db, bank_schema=bank_schema)
    return {
        "message": "Bank is created successfully",
        "data": result,
    }


@router.get("/list/", tags=["Bank"])
async def list_banks(
    page: int = Query(default=1, ge=1),
    size: int = Query(default=10, ge=1),
    name_i_contains: str | None = Query(default=None),
    db: AsyncSession = Depends(get_async_session),
):
    result = await BankCRUD.list_banks(
        db=db, page=page, size=size, name_i_contains=name_i_contains
    )

    return {
        "data": [BankListSchema.model_validate(i, from_attributes=True) for i in result]
    }


@router.get("/retrieve/{bank_id}/", tags=["Bank"])
async def retrieve_bank(bank: Bank = Depends(retrieve_bank_dependency)):
    return {"data": BankListSchema.model_validate(bank, from_attributes=True)}


@router.patch("/update/{bank_id}/", tags=["Bank"])
async def partial_update_bank(
    bank_schema: BankPartialUpdateSchema,
    bank: Bank = Depends(retrieve_bank_dependency),
    db: AsyncSession = Depends(get_async_session),
):
    result = await BankCRUD.partial_update_bank(
        db=db,
        bank_schema=bank_schema,
        bank=bank,
    )
    return {"data": BankListSchema.model_validate(result, from_attributes=True)}


@router.post("/{bank_id}/add/user/{user_id}/", tags=["Bank~Users"])
async def add_user_to_bank(
    bank: Bank = Depends(retrieve_bank_with_users_dependency),
    user: User = Depends(retrieve_user_dependency),
    db: AsyncSession = Depends(get_async_session),
):
    try:
        bank.users.append(user)
        await db.commit()
    except IntegrityError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User is already registered to this bank",
        )

    return {"message": "User added successfully"}
