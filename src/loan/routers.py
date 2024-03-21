from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
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
