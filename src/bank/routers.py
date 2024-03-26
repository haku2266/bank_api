from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from sqlalchemy import select, and_
from sqlalchemy.orm import joinedload


from src.auth.models import User
from src.auth.schemas import UserListSchema
from src.database import get_async_session

from src.bank.schemas import (
    BankCreateSchema,
    BankCreatedRetrieve,
    BankListSchema,
    BankPartialUpdateSchema,
)
from src.bank.crud import BankCRUD
from src.bank.models import Bank, BankUserAssociation
from src.bank.dependencies import (
    retrieve_bank_with_users_dependency,
    retrieve_bank_dependency,
)
from src.auth.routers import (
    retrieve_user_dependency,
    get_active_auth_user,
    get_teller_auth_user,
)

router = APIRouter(prefix="/bank")


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~PERMISSIONS~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
async def bank_id_that_is_relevant(
    bank_id: UUID,
    user: User = Depends(get_active_auth_user),
    db: AsyncSession = Depends(get_async_session),
) -> UUID:
    query = select(BankUserAssociation).where(
        and_(
            BankUserAssociation.user_id == user.id,
            BankUserAssociation.bank_id == bank_id,
        ),
    )
    result = await db.scalar(query)
    if result:
        return bank_id
    raise HTTPException(
        status_code=404,
        detail="Either the bank doesn't exist or the user is not a member of the bank",
    )


#  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ROUTERS~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
@router.post("/create/", tags=["Bank"])
async def create_bank(
    bank_schema: BankCreateSchema,
    db: AsyncSession = Depends(get_async_session),
    teller: User = Depends(get_teller_auth_user),
):
    result = await BankCRUD.create_bank(db=db, bank_schema=bank_schema)
    return {
        "message": "Bank is created successfully",
        "data": BankCreatedRetrieve.model_validate(result, from_attributes=True),
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
    teller: User = Depends(get_teller_auth_user),
):
    result = await BankCRUD.partial_update_bank(
        db=db,
        bank_schema=bank_schema,
        bank=bank,
    )
    return {"data": BankListSchema.model_validate(result, from_attributes=True)}


@router.post("/{bank_id}/user/add/{user_id}/", tags=["Bank~User"])
async def add_user_to_bank(
    bank: Bank = Depends(retrieve_bank_with_users_dependency),
    user: User = Depends(retrieve_user_dependency),
    db: AsyncSession = Depends(get_async_session),
    teller: User = Depends(get_teller_auth_user),
):
    try:
        if user.is_active:
            bank.users.append(user)
            await db.commit()
        else:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={"user_id": "Registration is unavailable. User is not active."},
            )
    except IntegrityError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"user_id": "User is already registered to this bank"},
        )

    return {
        "message": "User added successfully",
        "data": UserListSchema.model_validate(user, from_attributes=True),
    }


@router.get("/{bank_id}/user/list/", tags=["Bank~User"])
async def list_users_in_bank(
    bank: Bank = Depends(retrieve_bank_dependency),
    db: AsyncSession = Depends(get_async_session),
    teller: User = Depends(get_teller_auth_user),
):
    result = await BankCRUD.list_users_of_bank(db=db, bank=bank)
    print(result)
    return {
        "data": [UserListSchema.model_validate(i, from_attributes=True) for i in result]
    }


@router.delete(
    "/{bank_id}/user/delete/{user_id}/",
    tags=["Bank~User"],
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_user_from_bank(
    bank: Bank = Depends(retrieve_bank_with_users_dependency),
    user: User = Depends(retrieve_user_dependency),
    db: AsyncSession = Depends(get_async_session),
    teller: User = Depends(get_teller_auth_user),
):
    try:
        bank.users.remove(user)
        await db.commit()
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "user_id": f"user with id {user.id} is not registered in this bank"
            },
        )


@router.get("/me/banks/list/", tags=["User-Me-Bank"])
async def list_banks_user_me(
    user: User = Depends(get_active_auth_user),
    db: AsyncSession = Depends(get_async_session),
):
    query = (
        select(Bank.id, Bank.name, Bank.location)
        .select_from(Bank)
        .join(BankUserAssociation, onclause=Bank.id == BankUserAssociation.bank_id)
        .join(User, onclause=User.id == user.id)
    )

    banks = (await db.execute(query)).all()

    return {
        "data": [
            BankCreatedRetrieve.model_validate(bank, from_attributes=True)
            for bank in banks
        ],
    }


@router.get("/me/banks/{bank_id}/detail/", tags=["User-Me-Bank"])
async def detail_bank_user_me(
    bank_id: UUID = Depends(bank_id_that_is_relevant),
    user: User = Depends(get_active_auth_user),
    db: AsyncSession = Depends(get_async_session),
):
    bank = (
        await db.execute(
            select(Bank).options(joinedload(Bank.loan_types)).where(Bank.id == bank_id)
        )
    ).scalar()

    return {"data": BankListSchema.model_validate(bank, from_attributes=True)}


@router.post("/me/banks/{bank_id}/register/", tags=["User-Me-Bank"])
async def register_bank_user_me(
    bank: Bank = Depends(retrieve_bank_with_users_dependency),
    user: User = Depends(get_active_auth_user),
    db: AsyncSession = Depends(get_async_session),
):
    try:
        bank.users.append(user)
        await db.commit()
    except IntegrityError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="You are  already registered to this bank",
        )

    return {
        "message": "User added successfully",
        "data": UserListSchema.model_validate(user, from_attributes=True),
    }


@router.delete("/me/banks/{bank_id}/delete/", status_code=201, tags=["User-Me-Bank"])
async def delete_bank_user_me(
    bank: Bank = Depends(retrieve_bank_with_users_dependency),
    user: User = Depends(get_active_auth_user),
    db: AsyncSession = Depends(get_async_session),
):
    try:
        bank.users.remove(user)
        await db.commit()
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"you are not registered in this bank",
        )
