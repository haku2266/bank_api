from uuid import UUID

from fastapi import APIRouter, Depends, Path, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from src.account.dependencies import retrieve_account_dependency
from src.account.models import Deposit, Withdraw
from src.account.schemas import (
    AccountListSchema,
    AccountCreateSchema,
    DepositCreateSchema,
    DepositCreatedListSchema,
    WithdrawCreateSchema,
    WithdrawCreatedListSchema,
    DepositListSchema,
    WithdrawListSchema,
)
from src.auth.models import User
from src.auth.routers import get_active_auth_user, get_teller_auth_user
from src.bank.routers import bank_id_that_is_relevant
from src.database import get_async_session

from src.account.crud import AccountCRUD
from src.bank.models import Bank, Account
from src.bank.dependencies import retrieve_bank_dependency

router = APIRouter(prefix="/account")


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~PERMISSIONS~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
async def account_that_is_relevant(
    account_id: int,
    user: User = Depends(get_active_auth_user),
    db: AsyncSession = Depends(get_async_session),
) -> Account:
    query = select(Account).where(
        and_(
            Account.user_id == user.id,
            Account.id == account_id,
        )
    )

    result = await db.scalar(query)

    if not result:
        raise HTTPException(
            status_code=404,
            detail="Either the account doesn't exist or it doen't belong to this user",
        )

    return result


async def deposit_that_is_relevant(
    deposit_id: int,
    user: User = Depends(get_active_auth_user),
    db: AsyncSession = Depends(get_async_session),
):
    query = (
        select(Deposit)
        .select_from(Deposit)
        .join(Account, onclause=Account.id == Deposit.account_id)
        .where(and_(Account.user_id == user.id, Deposit.id == deposit_id))
    )

    result = await db.scalar(query)

    if not result:
        raise HTTPException(
            status_code=404,
            detail="Either the deposit doesn't exist or belong to this user",
        )
    return result


async def withdraw_that_is_relevant(
    withdraw_id: int,
    user: User = Depends(get_active_auth_user),
    db: AsyncSession = Depends(get_async_session),
):
    query = (
        select(Withdraw)
        .select_from(Withdraw)
        .join(Account, onclause=Account.id == Withdraw.account_id)
        .where(and_(Account.user_id == user.id, Withdraw.id == withdraw_id))
    )

    result = await db.scalar(query)

    if not result:
        raise HTTPException(
            status_code=404,
            detail="Either the withdraw doesn't exist or belong to this user",
        )
    return result


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ROUTERS~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
@router.get("/list/{bank_id}/", tags=["Bank~Account"])
async def list_accounts_in_bank(
    teller: User = Depends(get_teller_auth_user),
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
    teller: User = Depends(get_teller_auth_user),
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
    teller: User = Depends(get_teller_auth_user),
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
    teller: User = Depends(get_teller_auth_user),
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


@router.get("/me/banks/{bank_id}/accounts/list/", tags=["User-Me-Account"])
async def list_accounts_user_me(
    bank_id: UUID,
    user: User = Depends(get_active_auth_user),
    db: AsyncSession = Depends(get_async_session),
    teller: User = Depends(get_teller_auth_user),
):
    query = select(Account).where(
        and_(Account.bank_id == bank_id, Account.user_id == user.id)
    )

    result = await db.scalar(query)

    return {"data": AccountListSchema.model_validate(result, from_attributes=True)}


@router.post("/me/banks/{bank_id}/accounts/create/", tags=["User-Me-Account"])
async def create_account_user_me(
    money_schema: DepositCreateSchema,
    bank_id: UUID = Depends(bank_id_that_is_relevant),
    user: User = Depends(get_active_auth_user),
    db: AsyncSession = Depends(get_async_session),
    teller: User = Depends(get_teller_auth_user),
):

    account_schema = AccountCreateSchema(
        user_id=user.id, money=money_schema.model_dump()["amount"]
    )

    result = await AccountCRUD.create_account_in_bank(
        account_schema=account_schema, db=db, bank_id=bank_id
    )

    return {
        "message": "Account Created Successfully",
        "data": AccountListSchema.model_validate(result, from_attributes=True),
    }


@router.post(
    "/me/accounts/{account_id}/deposits/create/", tags=["User-Me-Account-Deposit"]
)
async def create_deposit_in_account(
    deposit_schema: DepositCreateSchema,
    account: Account = Depends(account_that_is_relevant),
    db: AsyncSession = Depends(get_async_session),
    teller: User = Depends(get_teller_auth_user),
):
    result = await AccountCRUD.create_deposit_in_account(
        db=db,
        account=account,
        deposit_schema=deposit_schema,
    )

    return {
        "message": "Deposit created successfully",
        "data": DepositCreatedListSchema.model_validate(result, from_attributes=True),
    }


@router.get(
    "/me/accounts/{account_id}/deposits/list/", tags=["User-Me-Account-Deposit"]
)
async def list_deposit_in_account_user_me(
    account: Account = Depends(account_that_is_relevant),
    db: AsyncSession = Depends(get_async_session),
):
    query = select(Deposit).where(Deposit.account_id == account.id)
    result = await db.scalars(query)

    return {
        "data": [
            DepositListSchema.model_validate(i, from_attributes=True) for i in result
        ]
    }


@router.get("/me/deposits/{deposit_id}/detail/", tags=["User-Me-Account-Deposit"])
async def retrieve_deposit_in_account_user_me(
    deposit: Deposit = Depends(deposit_that_is_relevant),
):

    return {"data": DepositListSchema.model_validate(deposit, from_attributes=True)}


@router.post(
    "/me/accounts/{account_id}/withdraws/create/", tags=["User-Me-Account-Withdraw"]
)
async def create_withdraw_in_account(
    withdraw_schema: WithdrawCreateSchema,
    account: Account = Depends(account_that_is_relevant),
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


@router.get(
    "/me/accounts/{account_id}/withdraws/list/", tags=["User-Me-Account-Withdraw"]
)
async def list_withdraw_in_account(
    account: Account = Depends(account_that_is_relevant),
    db: AsyncSession = Depends(get_async_session),
):
    query = select(Withdraw).where(Withdraw.account_id == account.id)
    result = await db.scalars(query)
    print(result)

    return {
        "data": [
            WithdrawListSchema.model_validate(i, from_attributes=True) for i in result
        ]
    }


@router.get("/me/withdraws/{withdraw_id}/detail/", tags=["User-Me-Account-Withdraw"])
async def retrieve_withdraw_in_account(
    withdraw: Deposit = Depends(withdraw_that_is_relevant),
):

    return {"data": WithdrawListSchema.model_validate(withdraw, from_attributes=True)}
