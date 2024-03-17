from uuid import UUID

from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from sqlalchemy import select, func, column
from sqlalchemy.orm import aliased, selectinload, joinedload

from src.auth.models import User
from src.bank.schemas import BankCreateSchema, BankPartialUpdateSchema
from src.bank.models import Bank, BankUserAssociation, Teller


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
