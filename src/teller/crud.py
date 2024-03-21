from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.auth.models import User

from src.bank.models import Bank
from src.teller.models import Teller


class TellerCRUD:

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
