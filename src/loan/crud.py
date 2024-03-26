from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import joinedload

from src.account.models import Account

from src.loan.models import LoanType, Loan, LoanCompensation

from src.loan.schemas import (
    LoanTypeCreateSchema,
    LoanCreateSchema,
    LoanCompensationCreateSchema,
)


class LoanCRUD:

    @staticmethod
    async def create_loan_type_in_bank(
        db: AsyncSession, loan_schema: LoanTypeCreateSchema
    ):
        data = loan_schema.model_dump()
        try:
            new_loan_type = LoanType(**data)
            db.add(new_loan_type)
            await db.commit()
            return new_loan_type
        except Exception as e:
            if "unique constraint" in str(e).lower():
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail={"name": f"loan with name '{data['name']}' already exists"},
                )

            raise HTTPException(
                status_code=400, detail={"bank_id": "bank_id is invalid"}
            )

    @staticmethod
    async def create_loan_in_account(
        db: AsyncSession, loan_schema: LoanCreateSchema, account_id: int
    ):
        data = loan_schema.model_dump()
        data["account_id"] = account_id
        try:
            loan_type = await db.scalar(
                select(LoanType).where(LoanType.id == data["loan_type_id"])
            )
            data["amount_expected"] = (loan_type.interest / 100 + 1) * data[
                "amount_out"
            ]
            new_loan = Loan(**data)

            db.add(new_loan)
            await db.commit()

            account = await db.scalar(select(Account).where(Account.id == account_id))

            account.money += data["amount_out"]

            await db.commit()

            return new_loan
        except Exception as e:
            if "loan_user_id_fkey" in str(e).lower():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={"user_id": f"user_id is invalid"},
                )
            elif "loan_loan_type_id_fkey" in str(e).lower():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={"user_id": f"loan_type_id is invalid"},
                )
            elif "loan_account_id_fkey" in str(e).lower():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={"user_id": "account_id is invalid"},
                )
            raise HTTPException(
                status_code=400,
                detail={
                    "message": f"{e} Invalid data. Check against (user_id, account_id, loan_type_id)."
                },
            )

    @staticmethod
    async def retrieve_loan(db: AsyncSession, loan_id: int) -> Loan | None:
        query = (
            select(Loan).options(joinedload(Loan.loan_type)).where(Loan.id == loan_id)
        )
        result = await db.scalar(query)

        return result

    @staticmethod
    async def create_loan_compensation(
        db: AsyncSession,
        loan: Loan,
        loan_compensation_schema: LoanCompensationCreateSchema,
    ):
        if loan.is_covered:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"message": "loan is totally covered"},
            )

        data: dict = loan_compensation_schema.model_dump()
        diff = loan.amount_expected - data.get("amount")
        if diff > 0:
            data["loan_id"] = loan.id
            loan.amount_expected -= data.get("amount")
            loan.amount_in += data.get("amount")
        elif diff == 0:
            data["loan_id"] = loan.id
            loan.amount_expected -= data.get("amount")
            loan.amount_in += data.get("amount")
            loan.is_covered = True
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "amount": f"The amount is over by {abs(diff)} ; expected up to {loan.amount_expected}"
                },
            )
        try:
            new_compensation = LoanCompensation(**data)
            db.add(new_compensation)
            await db.commit()

            return new_compensation

        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e),
            )
