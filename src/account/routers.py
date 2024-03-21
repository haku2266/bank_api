from uuid import UUID

from fastapi import APIRouter, Depends, Path
from sqlalchemy.ext.asyncio import AsyncSession

from src.account.dependencies import retrieve_account_dependency
from src.account.schemas import (
    AccountListSchema,
    AccountCreateSchema,
    DepositCreateSchema,
    DepositCreatedListSchema,
    WithdrawCreateSchema,
    WithdrawCreatedListSchema,
)
from src.database import get_async_session

from src.account.crud import AccountCRUD
from src.bank.models import Bank, Account
from src.bank.dependencies import retrieve_bank_dependency

router = APIRouter(prefix="/account")


@router.get("/list/{bank_id}/", tags=["Bank~Account"])
async def list_accounts_in_bank(
    bank: Bank = Depends(retrieve_bank_dependency),
    db: AsyncSession = Depends(get_async_session),
):
    result = await AccountCRUD.list_accounts_in_bank(db=db, bank=bank)
    return {
        "data": [
            AccountListSchema.model_validate(i, from_attributes=True) for i in result
        ],
    }


@router.post("/create/{bank_id}/", tags=["Bank~Account"])
async def create_account_in_bank(
    account_schema: AccountCreateSchema,
    bank_id: UUID,
    db: AsyncSession = Depends(get_async_session),
):
    result = await AccountCRUD.create_account_in_bank(
        account_schema=account_schema, db=db, bank_id=bank_id
    )

    return {
        "message": "Account Created Successfully",
        "data": AccountListSchema.model_validate(result, from_attributes=True),
    }


@router.post("/{account_id}/create/deposit/", tags=["Bank~Deposit"])
async def create_deposit_in_account(
    deposit_schema: DepositCreateSchema,
    account: Account = Depends(retrieve_account_dependency),
    db: AsyncSession = Depends(get_async_session),
):
    result = await AccountCRUD.create_deposit_in_account(
        db=db,
        account=account,
        deposit_schema=deposit_schema,
    )

    return {
        "message": "Depo created successfully",
        "data": DepositCreatedListSchema.model_validate(result, from_attributes=True),
    }


@router.post("/{account_id}/create/withdraw/", tags=["Bank~Withdraw"])
async def create_withdraw_in_account(
    withdraw_schema: WithdrawCreateSchema,
    account: Account = Depends(retrieve_account_dependency),
    db: AsyncSession = Depends(get_async_session),
):
    result = await AccountCRUD.create_withdraw_in_account(
        db=db,
        account=account,
        withdraw_schema=withdraw_schema,
    )

    return {
        "message": "Withdraw created successfully",
        "data": WithdrawCreatedListSchema.model_validate(result, from_attributes=True),
    }
