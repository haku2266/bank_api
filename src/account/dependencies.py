from uuid import UUID

from fastapi import HTTPException, status, Depends, Path
from typing import Annotated
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from src.account.models import Deposit, Withdraw
from src.auth.models import User
from src.database import get_async_session
from src.account.crud import AccountCRUD
from src.bank.models import Bank, Account


async def retrieve_account_dependency(
    account_id: int,
    db: AsyncSession = Depends(get_async_session),
) -> Account:
    result = await AccountCRUD.retrieve_account_in_bank(db=db, account_id=account_id)

    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"loan_id": f"Account with id {account_id} is not found"},
        )
    return result
