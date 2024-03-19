from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from src.auth.models import User
from src.auth.schemas import UserListSchema
from src.database import get_async_session

from src.bank.schemas import (
    BankCreateSchema,
    BankCreatedRetrieve,
    BankListSchema,
    BankPartialUpdateSchema,
    AccountListSchema,
    AccountCreateSchema,
    LoanTypeCreateSchema,
    LoanTypesListSchema,
    LoanCreateSchema,
    LoanListSchema,
    LoanCompensationCreateSchema,
    LoanCompensationListSchema,
    DepositCreateSchema,
    DepositCreatedListSchema,
    WithdrawCreateSchema,
    WithdrawCreatedListSchema,
)
from src.bank.crud import BankCRUD
from src.bank.models import Bank, Loan, Account
from src.bank.dependencies import (
    retrieve_bank_with_users_dependency,
    retrieve_bank_dependency,
    retrieve_bank_with_staff_dependency,
    retrieve_loan_dependency,
    retrieve_account_dependency,
)
from src.auth.dependencies import retrieve_user_dependency

router = APIRouter(prefix="/bank")


@router.post("/create/", tags=["Bank"])
async def create_bank(
    bank_schema: BankCreateSchema, db: AsyncSession = Depends(get_async_session)
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
):
    try:
        bank.users.remove(user)
        await db.commit()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "user_id": f"user with id {user.id} is not registered in this bank"
            },
        )


@router.get("/{bank_id}/teller/list/", tags=["Bank~Teller"])
async def list_tellers_in_bank(
    bank: Bank = Depends(retrieve_bank_dependency),
    db: AsyncSession = Depends(get_async_session),
):
    result = await BankCRUD.list_tellers_of_bank(db=db, bank=bank)
    print(result)
    return {
        "data": [UserListSchema.model_validate(i, from_attributes=True) for i in result]
    }


@router.post("/{bank_id}/teller/add/{user_id}/", tags=["Bank~Teller"])
async def add_teller_to_bank(
    bank: Bank = Depends(retrieve_bank_dependency),
    user: User = Depends(retrieve_user_dependency),
    db: AsyncSession = Depends(get_async_session),
):
    try:
        result = await BankCRUD.add_teller_to_bank(db=db, bank=bank, user=user)
        return {
            "message": "Teller added successfully",
            "data": UserListSchema.model_validate(result, from_attributes=True),
        }

    except IntegrityError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"user_id": "Teller is already registered to this bank"},
        )


@router.get("/{bank_id}/account/list/", tags=["Bank~Account"])
async def list_accounts_in_bank(
    bank: Bank = Depends(retrieve_bank_dependency),
    db: AsyncSession = Depends(get_async_session),
):
    result = await BankCRUD.list_accounts_in_bank(db=db, bank=bank)
    return {
        "data": [
            AccountListSchema.model_validate(i, from_attributes=True) for i in result
        ],
    }


@router.post("/account/create/", tags=["Bank~Account"])
async def create_account_in_bank(
    account_schema: AccountCreateSchema,
    db: AsyncSession = Depends(get_async_session),
):
    result = await BankCRUD.create_account_in_bank(account_schema=account_schema, db=db)

    return {
        "message": "Account Created Successfully",
        "data": AccountListSchema.model_validate(result, from_attributes=True),
    }


@router.post("/loan_type/create/", tags=["Bank~Loan"])
async def create_loan_type_in_bank(
    loan_type_schema: LoanTypeCreateSchema,
    db: AsyncSession = Depends(get_async_session),
):
    result = await BankCRUD.create_loan_type_in_bank(
        db=db, loan_schema=loan_type_schema
    )

    return {
        "message": "Loan Type Created Successfully",
        "data": LoanTypesListSchema.model_validate(result, from_attributes=True),
    }


@router.post("/{account_id}/loan/create/", tags=["Bank~Loan"])
async def create_loan_in_account(
    account_id: int,
    loan_schema: LoanCreateSchema,
    db: AsyncSession = Depends(get_async_session),
):
    result = await BankCRUD.create_loan_in_account(
        db=db, loan_schema=loan_schema, account_id=account_id
    )

    return {
        "message": "Loan issued successfully",
        "data": LoanListSchema.model_validate(result, from_attributes=True),
    }


@router.post("/{loan_id}/create/compensation/", tags=["Bank~Loan"])
async def create_loan_compensation(
    compensation_schema: LoanCompensationCreateSchema,
    loan: Loan = Depends(retrieve_loan_dependency),
    db: AsyncSession = Depends(get_async_session),
):
    result = await BankCRUD.create_loan_compensation(
        db=db,
        loan=loan,
        loan_compensation_schema=compensation_schema,
    )
    return {
        "message": "Loan compensation created successfully",
        "data": LoanCompensationListSchema.model_validate(result, from_attributes=True),
    }


@router.post("/account/{account_id}/create/deposit/", tags=["Bank~Deposit"])
async def create_deposit_in_account(
    deposit_schema: DepositCreateSchema,
    account: Account = Depends(retrieve_account_dependency),
    db: AsyncSession = Depends(get_async_session),
):
    result = await BankCRUD.create_deposit_in_account(
        db=db,
        account=account,
        deposit_schema=deposit_schema,
    )

    return {
        "message": "Depo created successfully",
        "data": DepositCreatedListSchema.model_validate(result, from_attributes=True),
    }


@router.post("/account/{account_id}/create/withdraw/", tags=["Bank~Withdraw"])
async def create_withdraw_in_account(
    withdraw_schema: WithdrawCreateSchema,
    account: Account = Depends(retrieve_account_dependency),
    db: AsyncSession = Depends(get_async_session),
):
    result = await BankCRUD.create_withdraw_in_account(
        db=db,
        account=account,
        withdraw_schema=withdraw_schema,
    )

    return {
        "message": "Withdraw created successfully",
        "data": WithdrawCreatedListSchema.model_validate(result, from_attributes=True),
    }
