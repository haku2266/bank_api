from uuid import UUID

from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from sqlalchemy import select, func, column
from sqlalchemy.orm import aliased, selectinload, joinedload

from src.auth.models import User
from src.bank.schemas import (
    BankCreateSchema,
    BankPartialUpdateSchema,
    AccountCreateSchema,
    LoanTypeCreateSchema,
    LoanCreateSchema,
    LoanCompensationListSchema,
    LoanCompensationCreateSchema,
    DepositCreateSchema,
    WithdrawCreateSchema,
)
from src.bank.models import (
    Bank,
    BankUserAssociation,
    Teller,
    Account,
    LoanType,
    Loan,
    LoanCompensation,
    Deposit,
    Withdraw,
)


class BankCRUD:

    @staticmethod
    async def create_bank(db: AsyncSession, bank_schema: BankCreateSchema) -> Bank:
        try:
            data = bank_schema.model_dump()
            new_bank = Bank(**data)

            db.add(new_bank)
            await db.commit()

            return new_bank
        except IntegrityError:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={"name": "bank with this name already exists"},
            )

    @staticmethod
    async def list_banks(
        db: AsyncSession,
        page: int = 1,
        size: int = 10,
        name_i_contains: str | None = None,
    ) -> list:
        offset = (page - 1) * size
        limit = size

        if name_i_contains is None:
            query = (
                select(Bank)
                .options(joinedload(Bank.loan_types))
                .order_by(Bank.id)
                .offset(offset)
                .limit(limit)
            )
        else:
            query = (
                select(Bank)
                .options(joinedload(Bank.loan_types))
                .where(Bank.name.icontains(f"%{name_i_contains}%"))
                .order_by(Bank.id)
                .offset(offset)
                .limit(limit)
            )

        result = (await db.execute(query)).unique().scalars().all()

        return list(result)

    @staticmethod
    async def retrieve_bank(db: AsyncSession, bank_id: UUID) -> Bank | None:
        query = (
            select(Bank).options(joinedload(Bank.loan_types)).where(Bank.id == bank_id)
        )

        result = await db.scalar(query)

        return result

    @staticmethod
    async def retrieve_bank_with_users(db: AsyncSession, bank_id: UUID) -> Bank | None:
        query = select(Bank).options(selectinload(Bank.users)).where(Bank.id == bank_id)
        result = await db.scalar(query)
        return result

    @staticmethod
    async def partial_update_bank(
        db: AsyncSession,
        bank_schema: BankPartialUpdateSchema,
        bank: Bank,
    ) -> Bank:
        new_data = bank_schema.model_dump(exclude_unset=True)
        try:
            for key, value in new_data.items():
                setattr(bank, key, value)

            # db.add(bank)
            await db.commit()
            return bank
        except IntegrityError as e:
            await db.rollback()
            if "unique constraint" in str(e).lower():
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail={
                        "name": f'bank with name \'{new_data["name"]}\' already exists'
                    },
                )

    @staticmethod
    async def delete_bank(db: AsyncSession, bank: Bank) -> None:
        await db.delete(bank)
        await db.commit()
        return None

    @staticmethod
    async def list_users_of_bank(db: AsyncSession, bank: Bank) -> list:
        query = (
            select(
                User.id,
                User.name,
                User.email,
                User.phone_number,
                User.accounts_number,
                User.is_active,
                User.created_at,
                User.updated_at,
            )
            .select_from(User)
            .join(BankUserAssociation, BankUserAssociation.user_id == User.id)
            .join(Bank, BankUserAssociation.bank_id == bank.id)
        )

        result = await db.execute(query)
        objs = result.unique().all()
        return list(objs)

    @staticmethod
    async def list_tellers_of_bank(db: AsyncSession, bank: Bank) -> list:
        query = (
            select(
                User.id,
                User.name,
                User.email,
                User.phone_number,
                User.accounts_number,
                User.is_active,
                User.created_at,
                User.updated_at,
            )
            .select_from(User)
            .join(Teller, Teller.user_id == User.id)
            .join(Bank, Teller.bank_id == bank.id)
        )

        result = await db.execute(query)
        objs = result.unique().all()
        return list(objs)

    @staticmethod
    async def add_teller_to_bank(db: AsyncSession, bank: Bank, user: User) -> User:
        new_teller = Teller(**{"bank_id": bank.id, "user_id": user.id})
        db.add(new_teller)
        await db.commit()
        return new_teller.user

    @staticmethod
    async def list_accounts_in_bank(db: AsyncSession, bank: Bank) -> list:
        query = select(
            Account.id, Account.user_id, Account.money, Account.created_at
        ).where(Account.bank_id == bank.id)

        result = (await db.execute(query)).all()

        return list(result)

    @staticmethod
    async def create_account_in_bank(
        db: AsyncSession,
        account_schema: AccountCreateSchema,
    ) -> Account:
        try:
            new_account = Account(**account_schema.model_dump())
            db.add(new_account)
            await db.commit()
            return new_account
        except Exception as e:
            raise HTTPException(
                status_code=400, detail={"message": "user_id or bank_id is invalid"}
            )

    @staticmethod
    async def retrieve_account_in_bank(
        db: AsyncSession, account_id: int
    ) -> Account | None:
        query = select(Account).where(Account.id == account_id)
        result = await db.scalar(query)
        return result

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

    @staticmethod
    async def create_deposit_in_account(
        db: AsyncSession,
        account: Account,
        deposit_schema: DepositCreateSchema,
    ):
        data = deposit_schema.model_dump()
        data["account_id"] = account.id

        try:
            new_deposit = Deposit(**data)
            account.money += data["amount"]

            db.add(new_deposit)
            await db.commit()

            return new_deposit
        except Exception as e:
            if "check_d_amount_gt_100k" in str(e).lower():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={"amount": "it needs to be greater than 100k"},
                )
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    @staticmethod
    async def create_withdraw_in_account(
        db: AsyncSession,
        account: Account,
        withdraw_schema: WithdrawCreateSchema,
    ):
        data = withdraw_schema.model_dump()
        data["account_id"] = account.id

        try:
            new_withdraw = Deposit(**data)
            diff = data["amount"] - account.money
            if diff > 0:
                raise HTTPException(
                    detail={"amount": f"it needs to be up to {diff}"},
                    status_code=status.HTTP_400_BAD_REQUEST,
                )
            account.money -= data["amount"]

            db.add(new_withdraw)
            await db.commit()

            return new_withdraw
        except Exception as e:
            if "check_w_amount_between_range" in str(e).lower():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={"amount": "it needs to be between 100 000 and 3 000 000"},
                )
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
