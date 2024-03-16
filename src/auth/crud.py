from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from sqlalchemy import select, func
from sqlalchemy.orm import aliased

from src.auth.schemas import UserList
from src.auth.models import User


class UserCRUD:
    @staticmethod
    async def create_user(
        user_data: dict,
        db: AsyncSession,
    ) -> User:
        try:
            new_user = User(**user_data)

            db.add(new_user)

            await db.commit()

            return new_user

        except IntegrityError:

            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={"phone_number": "user with this phone number already exists"},
            )

    @staticmethod
    async def list_users(db: AsyncSession, page: int = 1, size: int = 10) -> list:
        offset = (page - 1) * size
        limit = size

        u1 = aliased(User)
        query = (
            select(
                u1.id,
                u1.name,
                u1.email,
                u1.phone_number,
                u1.accounts_number,
                u1.is_active,
                u1.created_at,
                u1.updated_at,
            )
            .select_from(u1)
            .offset(offset)
            .limit(limit)
            .order_by(u1.id)
        )

        result = (await db.execute(query)).all()

        return list(result)
