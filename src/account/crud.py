from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.account.models import Deposit, Account, Withdraw
from src.account.schemas import (
    AccountCreateSchema,
    WithdrawCreateSchema,
    DepositCreateSchema,
)
from src.auth.models import User
from src.bank.models import Bank


class AccountCRUD:

    @staticmethod
    async def list_accounts_in_bank(db: AsyncSession, bank: Bank) -> list:
        query = select(
            Account.id, Account.user_id, Account.money, Account.created_at
        ).where(Account.bank_id == bank.id)

        result = (await db.execute(query)).all()

        return list(result)

    @staticmethod
    async def create_account_in_bank(
        bank_id: UUID,
        db: AsyncSession,
        account_schema: AccountCreateSchema,
    ) -> Account:

        data = account_schema.model_dump()

        data["bank_id"] = bank_id

        user_id = data["user_id"]

        try:
            user = await db.get(User, user_id)

            user.accounts_number += 1

            new_account = Account(**data)
            db.add(new_account)
            await db.commit()
            return new_account
        except Exception as e:
            if "unique_account_in_bank" in str(e).lower():
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail={"user_id": "User already has an account in this bank"},
                )
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
            new_withdraw = Withdraw(**data)
            diff = data["amount"] - account.money
            if account.money == 0:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={"message": "the account has no money"},
                )
            elif diff > 0:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={"amount": "it needs to be up to {}".format(account.money)},
                )
            else:
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
