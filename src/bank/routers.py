from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from src.database import get_async_session

from src.bank.schemas import BankCreateSchema, BankCreatedRetrieve, BankListSchema
from src.bank.crud import BankCRUD

router = APIRouter(prefix="/bank", tags=["Bank"])


@router.post("/create", response_model=BankCreatedRetrieve)
async def create_bank(
    bank_schema: BankCreateSchema, db: AsyncSession = Depends(get_async_session)
):
    result = await BankCRUD.create_bank(db=db, bank_schema=bank_schema)
    return result


@router.get("/list/", response_model=list[BankListSchema])
async def list_banks(
    page: int = 1,
    size: int = 10,
    db: AsyncSession = Depends(get_async_session),
):
    result = await BankCRUD.list_banks(db=db, page=page, size=size)

    return result
