from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.account.routers import account_that_is_relevant
from src.account.models import Account
from src.auth.routers import get_active_auth_user, get_teller_auth_user, get_super_user
from src.auth.models import User
from src.database import get_async_session

from src.loan.crud import LoanCRUD
from src.loan.dependencies import retrieve_loan_dependency
from src.loan.models import Loan

from src.loan.schemas import (
    LoanTypeCreateSchema,
    LoanTypesListSchema,
    LoanCreateSchema,
    LoanListSchema,
    LoanCompensationCreateSchema,
    LoanCompensationListSchema,
)

router = APIRouter(prefix="/bank")


@router.post("/loan_type/create/", tags=["Bank~Loan"])
async def create_loan_type_in_bank(
    loan_type_schema: LoanTypeCreateSchema,
    db: AsyncSession = Depends(get_async_session),
    super_user: User = Depends(get_super_user),
):
    result = await LoanCRUD.create_loan_type_in_bank(
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
    teller: User = Depends(get_teller_auth_user),
):
    result = await LoanCRUD.create_loan_in_account(
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
    teller: User = Depends(get_teller_auth_user),
):
    result = await LoanCRUD.create_loan_compensation(
        db=db,
        loan=loan,
        loan_compensation_schema=compensation_schema,
    )
    return {
        "message": "Loan compensation created successfully",
        "data": LoanCompensationListSchema.model_validate(result, from_attributes=True),
    }


@router.get("/me/loans/", tags=["User-Me-Loan"])
async def list_loans_user_me(
    user: User = Depends(get_active_auth_user),
    db: AsyncSession = Depends(get_async_session),
):
    query = (
        select(Loan)
        .select_from(Loan)
        .where(
            Loan.account_id.in_(
                select(Account.id)
                .select_from(Account)
                .where(Account.user_id == user.id)
            )
        )
    )
    result = await db.scalars(query)
    print(result)

    return {
        "data": [LoanListSchema.model_validate(i, from_attributes=True) for i in result]
    }


@router.get("/me/{account_id}/loans/list/", tags=["User-Me-Loan"])
async def list_loans_in_account_user_me(
    account: Account = Depends(account_that_is_relevant),
    db: AsyncSession = Depends(get_async_session),
):
    query = select(Loan).where(Loan.account_id == account.id)

    result = await db.scalars(query)

    return {
        "data": [LoanListSchema.model_validate(i, from_attributes=True) for i in result]
    }


@router.post("/me/{account_id}/loans/apply/", tags=["User-Me-Loan"])
async def apply_for_loan_in_account_user_me(
    loan_schema: LoanCreateSchema,
    account: Account = Depends(account_that_is_relevant),
    db: AsyncSession = Depends(get_async_session),
):
    result = await LoanCRUD.create_loan_in_account(
        db=db, loan_schema=loan_schema, account_id=account.id
    )

    return {
        "message": "Loan issued successfully",
        "data": LoanListSchema.model_validate(result, from_attributes=True),
    }
