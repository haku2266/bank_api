from uuid import UUID

from fastapi import HTTPException, status, Depends, Path
from typing import Annotated
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_async_session
from src.bank.crud import BankCRUD
from src.bank.models import Bank, Loan, Account


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


async def retrieve_bank_with_staff_dependency(
    bank_id: UUID,
    db: AsyncSession = Depends(get_async_session),
) -> Bank:
    result = await BankCRUD.retrieve_bank_with_staff(db=db, bank_id=bank_id)
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


async def retrieve_loan_dependency(
    loan_id: int,
    db: AsyncSession = Depends(get_async_session),
) -> Loan:
    result = await BankCRUD.retrieve_loan(db=db, loan_id=loan_id)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"loan_id": f"Loan with id {loan_id} is not found"},
        )
    return result


async def retrieve_account_dependency(
    account_id: int,
    db: AsyncSession = Depends(get_async_session),
) -> Account:
    result = await BankCRUD.retrieve_account_in_bank(db=db, account_id=account_id)

    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"loan_id": f"Account with id {account_id} is not found"},
        )
    return result
