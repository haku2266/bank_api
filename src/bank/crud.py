from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from sqlalchemy import select, func
from sqlalchemy.orm import aliased, selectinload, joinedload

from src.bank.schemas import BankCreateSchema
from src.bank.models import Bank


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
    async def list_banks(db: AsyncSession, page: int = 1, size: int = 10) -> list:
        offset = (page - 1) * size
        limit = size

        query = (
            select(Bank)
            .options(joinedload(Bank.loan_types))
            .order_by(Bank.id)
            .offset(offset)
            .limit(limit)
        )

        result = (await db.execute(query)).unique().scalars().all()

        return list(result)
