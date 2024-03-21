from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from src.auth.models import User
from src.auth.schemas import UserListSchema
from src.bank.dependencies import retrieve_bank_dependency
from src.database import get_async_session

from src.teller.crud import TellerCRUD
from src.bank.models import Bank

from src.auth.dependencies import retrieve_user_dependency

router = APIRouter(prefix="/teller")


@router.get("/list/{bank_id}/", tags=["Bank~Teller"])
async def list_tellers_in_bank(
    bank: Bank = Depends(retrieve_bank_dependency),
    db: AsyncSession = Depends(get_async_session),
):
    result = await TellerCRUD.list_tellers_of_bank(db=db, bank=bank)
    print(result)
    return {
        "data": [UserListSchema.model_validate(i, from_attributes=True) for i in result]
    }


@router.post("/add/{bank_id}/{user_id}/", tags=["Bank~Teller"])
async def add_teller_to_bank(
    bank: Bank = Depends(retrieve_bank_dependency),
    user: User = Depends(retrieve_user_dependency),
    db: AsyncSession = Depends(get_async_session),
):
    try:
        result = await TellerCRUD.add_teller_to_bank(db=db, bank=bank, user=user)
        return {
            "message": "Teller added successfully",
            "data": UserListSchema.model_validate(result, from_attributes=True),
        }

    except IntegrityError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"user_id": "Teller is already registered to this bank"},
        )
