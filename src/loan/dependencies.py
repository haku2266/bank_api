from uuid import UUID

from fastapi import HTTPException, status, Depends, Path
from typing import Annotated
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_async_session
from src.loan.crud import LoanCRUD
from src.loan.models import Loan


async def retrieve_loan_dependency(
    loan_id: int,
    db: AsyncSession = Depends(get_async_session),
) -> Loan:
    result = await LoanCRUD.retrieve_loan(db=db, loan_id=loan_id)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"loan_id": f"Loan with id {loan_id} is not found"},
        )
    return result

