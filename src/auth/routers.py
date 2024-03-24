from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Query, Form, Body
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from sqlalchemy import select, and_
from sqlalchemy.orm import selectinload, joinedload

from fastapi.security import (
    HTTPBearer,
    HTTPAuthorizationCredentials,
)
from jwt.exceptions import ExpiredSignatureError, DecodeError

from src.account.crud import AccountCRUD
from src.account.dependencies import retrieve_account_dependency
from src.account.models import Account, Deposit, Withdraw
from src.account.schemas import (
    AccountListSchema,
    AccountCreateSchema,
    DepositCreateSchema,
    DepositCreatedListSchema,
    DepositListSchema,
    WithdrawCreateSchema,
    WithdrawCreatedListSchema,
    WithdrawListSchema,
)
from src.auth.models import User
from src.auth.schemas import (
    UserCreateSchema,
    UserListSchema,
    UserPartialUpdateSchema,
    TokenInfo,
)
from src.auth.utils import (
    hash_password,
    generate_validation_code,
    store_validation_code,
    send_email,
    retrieve_validation_code,
    encode_jwt,
    decode_jwt,
)
from src.auth.crud import UserCRUD
from src.bank.dependencies import retrieve_bank_with_users_dependency
from src.bank.models import Bank, BankUserAssociation
from src.bank.schemas import BankListSchema, BankCreatedRetrieve
from src.database import get_async_session
from src.auth.dependencies import retrieve_user_dependency, validate_user
from src.loan.crud import LoanCRUD
from src.loan.models import Loan
from src.loan.schemas import LoanListSchema, LoanCreateSchema

router = APIRouter(prefix="/user")

http_bearer = HTTPBearer()


@router.post("/access_token/", tags=["Tokens"])
async def issue_access_token(
    user: UserListSchema = Depends(validate_user),
) -> TokenInfo:
    print("worked")
    access_payload = {
        "sub": user.id,
        "phone_number": user.phone_number,
        "email": user.email,
    }

    refresh_payload = {
        "sub": user.id,
        "is_refresh": True,
    }

    access_token = encode_jwt(payload=access_payload)
    refresh_token = encode_jwt(payload=refresh_payload, expire_minutes=60)

    return TokenInfo(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="Bearer",
    )


@router.post("/refresh_token/", tags=["Tokens"])
async def issue_refresh_token(
    credentials: HTTPAuthorizationCredentials = Depends(http_bearer),
    db: AsyncSession = Depends(get_async_session),
):
    try:
        ref_token = credentials.credentials
        payload = decode_jwt(ref_token)
        user_id = payload.get("sub")
        check = payload.get("is_refresh")
        if not check:
            raise HTTPException(status_code=401, detail="refresh token invalid")
        user = await db.get(User, user_id)
        new_payload = {
            "sub": user.id,
            "phone_number": user.phone_number,
            "email": user.email,
        }
        access_token = encode_jwt(payload=new_payload)

        return TokenInfo(
            access_token=access_token,
            refresh_token=ref_token,
            token_type="Bearer",
        )

    except ExpiredSignatureError:
        raise HTTPException(status_code=401, detail=f"refresh token is expired")
    except DecodeError:
        raise HTTPException(status_code=401, detail="refresh token invalid")


async def get_curr_auth_user(
    credentials: HTTPAuthorizationCredentials = Depends(http_bearer),
    db: AsyncSession = Depends(get_async_session),
) -> User | None:
    try:
        token = credentials.credentials
        payload = decode_jwt(token)
        user_id = payload.get("sub")
        user = await db.get(User, user_id)
        return user

    except ExpiredSignatureError:
        raise HTTPException(status_code=401, detail=f"token is expired")
    except DecodeError:
        raise HTTPException(status_code=401, detail="invalid token")


def get_active_auth_user(user: User = Depends(get_curr_auth_user)) -> User:
    if user.is_active:
        return user
    raise HTTPException(
        status_code=403,
        detail="Only active users are allowed to access this resource",
    )


def get_teller_auth_user(user: User = Depends(get_active_auth_user)) -> User:
    if user.is_teller:
        return user
    raise HTTPException(
        status_code=403,
        detail="Only tellers are allowed to access this resource",
    )


def get_super_user(user: User = Depends(get_active_auth_user)) -> User:
    if user.is_superuser:
        return user
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Only superusers can access this resource",
    )


async def bank_id_that_is_relevant(
    bank_id: UUID,
    user: User = Depends(get_active_auth_user),
    db: AsyncSession = Depends(get_async_session),
) -> UUID:
    query = select(BankUserAssociation).where(
        and_(
            BankUserAssociation.user_id == user.id,
            BankUserAssociation.bank_id == bank_id,
        ),
    )
    result = await db.scalar(query)
    if result:
        return bank_id
    raise HTTPException(
        status_code=404,
        detail="Either the bank doesn't exist or the user is not a member of the bank",
    )


async def account_that_is_relevant(
    account_id: int,
    user: User = Depends(get_active_auth_user),
    db: AsyncSession = Depends(get_async_session),
) -> Account:
    query = select(Account).where(
        and_(Account.user_id == user.id), Account.id == account_id
    )

    result = await db.scalar(query)

    if not result:
        raise HTTPException(
            status_code=404,
            detail="Either the account doesn't exist or it doen't belong to this user",
        )

    return result


async def deposit_that_is_relevant(
    deposit_id: int,
    user: User = Depends(get_active_auth_user),
    db: AsyncSession = Depends(get_async_session),
):
    query = (
        select(Deposit)
        .select_from(Deposit)
        .join(Account, onclause=Account.id == Deposit.account_id)
        .where(and_(Account.user_id == user.id, Deposit.id == deposit_id))
    )

    result = await db.scalar(query)

    if not result:
        raise HTTPException(
            status_code=404,
            detail="Either the deposit doesn't exist or belong to this user",
        )
    return result


async def withdraw_that_is_relevant(
    withdraw_id: int,
    user: User = Depends(get_active_auth_user),
    db: AsyncSession = Depends(get_async_session),
):
    query = (
        select(Withdraw)
        .select_from(Withdraw)
        .join(Account, onclause=Account.id == Withdraw.account_id)
        .where(and_(Account.user_id == user.id, Withdraw.id == withdraw_id))
    )

    result = await db.scalar(query)

    if not result:
        raise HTTPException(
            status_code=404,
            detail="Either the withdraw doesn't exist or belong to this user",
        )
    return result


@router.post("/create/", status_code=201, tags=["User"])
async def create_user(
    user_schema: UserCreateSchema, db: AsyncSession = Depends(get_async_session)
):
    data = user_schema.model_dump()
    password = data.pop("password")
    data.update({"hashed_password": hash_password(password)})

    result = await UserCRUD.create_user(user_data=data, db=db)

    return {
        "message": "User created successfully. To activate your account, check your gmail.",
        "data": UserListSchema.model_validate(result, from_attributes=True),
    }


@router.get("/list/", tags=["User"])
async def list_users(
    teller: User = Depends(get_teller_auth_user),
    db: AsyncSession = Depends(get_async_session),
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1),
):
    result = await UserCRUD.list_users(db=db, page=page, size=size)

    return {
        "page": page,
        "size": size,
        "data": [
            UserListSchema.model_validate(user, from_attributes=True) for user in result
        ],
    }


@router.get("/retrieve/{user_id}/", tags=["User"])
async def retrieve_user(
    teller: User = Depends(get_teller_auth_user),
    user: User = Depends(retrieve_user_dependency),
):
    return {
        "data": UserListSchema.model_validate(user, from_attributes=True),
    }


@router.patch("/update/{user_id}/", tags=["User"])
async def partial_update_user(
    user_schema: UserPartialUpdateSchema,
    db: AsyncSession = Depends(get_async_session),
    user: User = Depends(retrieve_user_dependency),
    teller: User = Depends(get_teller_auth_user),
):
    result = await UserCRUD.partial_update_user(
        db=db, user_schema=user_schema, user=user
    )
    return {"data": UserListSchema.model_validate(result, from_attributes=True)}


@router.delete(
    "/delete/{user_id}/", status_code=status.HTTP_204_NO_CONTENT, tags=["User"]
)
async def delete_user(
    user: User = Depends(retrieve_user_dependency),
    db: AsyncSession = Depends(get_async_session),
    teller: User = Depends(get_teller_auth_user),
):
    result = await UserCRUD.delete_user(db=db, user=user)
    return None


@router.get("/me/", tags=["User-Me"])
async def retrieve_user_me(
    user: User = Depends(get_active_auth_user),
    db: AsyncSession = Depends(get_async_session),
):
    return {"data": UserListSchema.model_validate(user, from_attributes=True)}


@router.get("/me/banks/list/", tags=["User-Me-Bank"])
async def list_banks_user_me(
    user: User = Depends(get_active_auth_user),
    db: AsyncSession = Depends(get_async_session),
):
    query = (
        select(Bank.id, Bank.name, Bank.location)
        .select_from(Bank)
        .join(BankUserAssociation, onclause=Bank.id == BankUserAssociation.bank_id)
        .join(User, onclause=User.id == user.id)
    )

    banks = (await db.execute(query)).all()

    return {
        "data": [
            BankCreatedRetrieve.model_validate(bank, from_attributes=True)
            for bank in banks
        ],
    }


@router.get("/me/banks/{bank_id}/detail/", tags=["User-Me-Bank"])
async def detail_bank_user_me(
    bank_id: UUID = Depends(bank_id_that_is_relevant),
    user: User = Depends(get_active_auth_user),
    db: AsyncSession = Depends(get_async_session),
):
    bank = (
        await db.execute(
            select(Bank).options(joinedload(Bank.loan_types)).where(Bank.id == bank_id)
        )
    ).scalar()

    return {"data": BankListSchema.model_validate(bank, from_attributes=True)}


@router.post("/me/banks/{bank_id}/register/", tags=["User-Me-Bank"])
async def register_bank_user_me(
    bank: Bank = Depends(retrieve_bank_with_users_dependency),
    user: User = Depends(get_active_auth_user),
    db: AsyncSession = Depends(get_async_session),
):
    try:
        bank.users.append(user)
        await db.commit()
    except IntegrityError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="You are  already registered to this bank",
        )

    return {
        "message": "User added successfully",
        "data": UserListSchema.model_validate(user, from_attributes=True),
    }


@router.delete("/me/banks/{bank_id}/delete/", status_code=201, tags=["User-Me-Bank"])
async def delete_bank_user_me(
    bank: Bank = Depends(retrieve_bank_with_users_dependency),
    user: User = Depends(get_active_auth_user),
    db: AsyncSession = Depends(get_async_session),
):
    try:
        bank.users.remove(user)
        await db.commit()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"you are not registered in this bank",
        )


@router.get("/me/banks/{bank_id}/accounts/list/", tags=["User-Me-Account"])
async def list_accounts_user_me(
    bank_id: UUID,
    user: User = Depends(get_active_auth_user),
    db: AsyncSession = Depends(get_async_session),
):
    query = select(Account).where(
        and_(Account.bank_id == bank_id, Account.user_id == user.id)
    )

    result = await db.scalar(query)

    return {"data": AccountListSchema.model_validate(result, from_attributes=True)}


@router.post("/me/banks/{bank_id}/accounts/create/", tags=["User-Me-Account"])
async def create_account_user_me(
    money_schema: DepositCreateSchema,
    bank_id: UUID = Depends(bank_id_that_is_relevant),
    user: User = Depends(get_active_auth_user),
    db: AsyncSession = Depends(get_async_session),
):

    account_schema = AccountCreateSchema(user_id=user.id, money=money_schema.model_dump()["amount"])

    result = await AccountCRUD.create_account_in_bank(
        account_schema=account_schema, db=db, bank_id=bank_id
    )

    return {
        "message": "Account Created Successfully",
        "data": AccountListSchema.model_validate(result, from_attributes=True),
    }


@router.post(
    "/me/accounts/{account_id}/deposits/create/", tags=["User-Me-Account-Deposit"]
)
async def create_deposit_in_account(
    deposit_schema: DepositCreateSchema,
    account: Account = Depends(account_that_is_relevant),
    db: AsyncSession = Depends(get_async_session),
):
    result = await AccountCRUD.create_deposit_in_account(
        db=db,
        account=account,
        deposit_schema=deposit_schema,
    )

    return {
        "message": "Deposit created successfully",
        "data": DepositCreatedListSchema.model_validate(result, from_attributes=True),
    }


@router.get(
    "/me/accounts/{account_id}/deposits/list/", tags=["User-Me-Account-Deposit"]
)
async def list_deposit_in_account(
    account: Account = Depends(account_that_is_relevant),
    db: AsyncSession = Depends(get_async_session),
):
    query = select(Deposit).where(Deposit.account_id == account.id)
    result = await db.scalars(query)

    return {
        "data": [
            DepositListSchema.model_validate(i, from_attributes=True) for i in result
        ]
    }


@router.get("/me/deposits/{deposit_id}/detail/", tags=["User-Me-Account-Deposit"])
async def retrieve_deposit_in_account(
    deposit: Deposit = Depends(deposit_that_is_relevant),
    db: AsyncSession = Depends(get_async_session),
):

    return {"data": DepositListSchema.model_validate(deposit, from_attributes=True)}


@router.post(
    "/me/accounts/{account_id}/withdraws/create/", tags=["User-Me-Account-Withdraw"]
)
async def create_withdraw_in_account(
    withdraw_schema: WithdrawCreateSchema,
    account: Account = Depends(account_that_is_relevant),
    db: AsyncSession = Depends(get_async_session),
):
    result = await AccountCRUD.create_withdraw_in_account(
        db=db,
        account=account,
        withdraw_schema=withdraw_schema,
    )

    return {
        "message": "Withdraw created successfully",
        "data": WithdrawCreatedListSchema.model_validate(result, from_attributes=True),
    }


@router.get(
    "/me/accounts/{account_id}/withdraws/list/", tags=["User-Me-Account-Withdraw"]
)
async def list_withdraw_in_account(
    account: Account = Depends(account_that_is_relevant),
    db: AsyncSession = Depends(get_async_session),
):
    query = select(Withdraw).where(Withdraw.account_id == account.id)
    result = await db.scalars(query)
    print(result)

    return {
        "data": [
            WithdrawListSchema.model_validate(i, from_attributes=True) for i in result
        ]
    }


@router.get("/me/withdraws/{withdraw_id}/detail/", tags=["User-Me-Account-Withdraw"])
async def retrieve_withdraw_in_account(
    withdraw: Deposit = Depends(withdraw_that_is_relevant),
    db: AsyncSession = Depends(get_async_session),
):

    return {"data": WithdrawListSchema.model_validate(withdraw, from_attributes=True)}


@router.patch("/me/update/", tags=["User-Me"])
async def update_user_me(
    user_schema: UserPartialUpdateSchema,
    db: AsyncSession = Depends(get_async_session),
    user: User = Depends(get_active_auth_user),
):
    result = await UserCRUD.partial_update_user(
        db=db, user_schema=user_schema, user=user
    )
    return {"data": UserListSchema.model_validate(result, from_attributes=True)}


@router.delete("/me/delete/", status_code=201, tags=["User-Me"])
async def delete_user_me(
    user: User = Depends(get_active_auth_user),
    db: AsyncSession = Depends(get_async_session),
):
    result = await UserCRUD.delete_user(db=db, user=user)
    return None


@router.get("/me/loans/", tags=["User-Me-Loan"])
async def list_loans_user_me(
    user: User = Depends(get_active_auth_user),
    db: AsyncSession = Depends(get_async_session),
):
    query = (
        select(Loan)
        .select_from(Loan)
        .where(
            Loan.account_id.in_(
                select(Account.id)
                .select_from(Account)
                .where(Account.user_id == user.id)
            )
        )
    )
    result = await db.scalars(query)
    print(result)

    return {
        "data": [LoanListSchema.model_validate(i, from_attributes=True) for i in result]
    }


@router.get("/me/{account_id}/loans/list/", tags=["User-Me-Loan"])
async def list_loans_in_account_user_me(
    account: Account = Depends(account_that_is_relevant),
    db: AsyncSession = Depends(get_async_session),
):
    query = select(Loan).where(Loan.account_id == account.id)

    result = await db.scalars(query)

    return {
        "data": [LoanListSchema.model_validate(i, from_attributes=True) for i in result]
    }


@router.post("/me/{account_id}/loans/apply/", tags=["User-Me-Loan"])
async def apply_for_loan_in_account_user_me(
    loan_schema: LoanCreateSchema,
    account: Account = Depends(account_that_is_relevant),
    db: AsyncSession = Depends(get_async_session),
):
    result = await LoanCRUD.create_loan_in_account(
        db=db, loan_schema=loan_schema, account_id=account.id
    )

    return {
        "message": "Loan issued successfully",
        "data": LoanListSchema.model_validate(result, from_attributes=True),
    }


@router.get("/me/loans/{loan_id}/", tags=["User-Me-Loan"])
async def retrieve_loan_user_me():
    pass


@router.get("/me/loans/{loan_id}/compensations/list/", tags=["User-Me-Loan"])
async def list_loan_compensations_user_me():
    pass


@router.post("/me/loans/{loan_id}/compensations/create/", tags=["User-Me-Loan"])
async def create_loan_compensation_user_me():
    pass


@router.get("/me/compensations/{compensation_id}/detail/", tags=["User-Me-Loan"])
async def retrieve_compensations_user_me():
    pass


@router.get("/me/{bank_id}/loan_types/list/", tags=["User-Me-Loan-Type"])
async def list_loan_types_user_me():
    pass


@router.get("/me//loan_types/{loan_type_id}/detail/", tags=["User-Me-Loan-Type"])
async def retrieve_loan_types_user_me():
    pass


@router.post("/activate/", tags=["User"])
async def activate_user(
    email: str,
    db: AsyncSession = Depends(get_async_session),
):
    query = select(User).where(User.email == email)
    user = await db.scalar(query)
    if not user.is_active:

        validation_code = generate_validation_code()
        store_validation_code(
            email, validation_code, expiration_time=600
        )  # Set expiration time (in seconds)
        send_email(email, validation_code, name=user.name)

        return {"message": "Email has been sent", "email": email}

    else:
        raise HTTPException(
            status_code=404, detail={"message": "User is already active"}
        )

        # API endpoint to validate code


@router.post("/validate/activation_code/", tags=["User"])
async def validate_activation_code(
    code: str,
    email: str,
    db: AsyncSession = Depends(get_async_session),
):
    query = select(User).where(User.email == email)
    user = await db.scalar(query)

    if not user:
        raise HTTPException(
            status_code=404, detail="User is not found. Check credentials"
        )

    if not user.is_active:
        stored_code = retrieve_validation_code(email)
        if stored_code.decode("utf-8") == code:
            user.is_active = True
            await db.commit()
            return {"message": "User is activated!"}
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Invalid activation code",
            )
    else:
        raise HTTPException(
            status_code=404, detail={"message": "User is already active"}
        )
