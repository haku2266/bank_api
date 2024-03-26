from uuid import UUID

from fastapi import HTTPException, status, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from src.auth.routers import get_active_auth_user
from src.auth.models import User
from src.database import get_async_session
from src.bank.crud import BankCRUD
from src.bank.models import Bank, BankUserAssociation


async def retrieve_bank_with_users_dependency(
    bank_id: UUID,
    db: AsyncSession = Depends(get_async_session),
) -> Bank:
    result = await BankCRUD.retrieve_bank_with_users(db=db, bank_id=bank_id)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"id": f"Bank with id {bank_id} is not found"},
        )
    return result


async def retrieve_bank_dependency(
    bank_id: UUID,
    db: AsyncSession = Depends(get_async_session),
) -> Bank:
    result = await BankCRUD.retrieve_bank(db=db, bank_id=bank_id)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"id": f"Bank with id {bank_id} is not found"},
        )
    return result

