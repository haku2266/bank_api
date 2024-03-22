from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select


from src.auth.models import User
from src.auth.schemas import UserCreateSchema, UserListSchema, UserPartialUpdateSchema
from src.auth.utils import (
    hash_password,
    generate_validation_code,
    store_validation_code,
    send_email,
    retrieve_validation_code,
)
from src.auth.crud import UserCRUD
from src.database import get_async_session
from src.auth.dependencies import retrieve_user_dependency

router = APIRouter(prefix="/user")


# @router.post("/access_token/")
# async def issue_jwt(user: UserLoginSchema = Depends(validate_user)) -> TokenInfo:
#     print("worked")
#     access_payload = {
#         "sub": user.username,
#         "username": user.username,
#         "email": user.email,
#     }
#
#     refresh_payload = {
#         "sub": user.username,
#         "is_refresh": True,
#     }
#
#     access_token = encode_jwt(payload=access_payload)
#     refresh_token = encode_jwt(payload=refresh_payload, expire_mins=60)
#
#     return TokenInfo(
#         access_token=access_token,
#         refresh_token=refresh_token,
#         token_type="Bearer",
#     )


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
async def retrieve_user(user: User = Depends(retrieve_user_dependency)):
    return {
        "data": UserListSchema.model_validate(user, from_attributes=True),
    }


@router.patch("/update/{user_id}/", tags=["User"])
async def partial_update_user(
    user_schema: UserPartialUpdateSchema,
    db: AsyncSession = Depends(get_async_session),
    user: User = Depends(retrieve_user_dependency),
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
):
    result = await UserCRUD.delete_user(db=db, user=user)
    return None


@router.get("/me/", tags=["User-Me"])
async def retrieve_user_me(db: AsyncSession = Depends(get_async_session)):
    pass


@router.post("/activate/", tags=["User"])
async def activate_user(email: str):

    validation_code = generate_validation_code()
    store_validation_code(
        email, validation_code, expiration_time=600
    )  # Set expiration time (in seconds)
    send_email(email, validation_code)

    return {"message": "Email has been sent"}

    # API endpoint to validate code


@router.post("/validate/activation_code/")
async def validate_activation_code(
    code: str,
    email: str,
    db: AsyncSession = Depends(get_async_session),
):
    query = select(User).where(User.email == email)
    user = await db.scalar(query)

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


@router.get("/me/banks/list/", tags=["User-Me-Bank"])
async def list_banks_user_me():
    pass


@router.get("/me/banks/{bank_id}/detail/", tags=["User-Me-Bank"])
async def detail_bank_user_me():
    pass


@router.post("/me/banks/register/", tags=["User-Me-Bank"])
async def register_bank_user_me():
    pass


@router.delete("/me/banks/{bank_id}/delete/", tags=["User-Me-Bank"])
async def delete_bank_user_me():
    pass


@router.get("/me/banks/{bank_id}/accounts/list/", tags=["User-Me-Account"])
async def list_accounts_user_me():
    pass


@router.post("/me/banks/{bank_id}/accounts/create/", tags=["User-Me-Account"])
async def create_account_user_me():
    pass


@router.get("/me/accounts/{account_id}/detail/", tags=["User-Me-Account"])
async def detail_account_user_me():
    pass


@router.post(
    "/me/accounts/{account_id}/deposits/create/", tags=["User-Me-Account-Deposit"]
)
async def create_deposit_in_account():
    pass


@router.get(
    "/me/accounts/{account_id}/deposits/list/", tags=["User-Me-Account-Deposit"]
)
async def list_deposit_in_account():
    pass


@router.get("/me/deposits/{deposit_id}/", tags=["User-Me-Account-Deposit"])
async def retrieve_deposit_in_account():
    pass


@router.post(
    "/me/accounts/{account_id}/withdraws/create/", tags=["User-Me-Account-Withdraw"]
)
async def create_withdraw_in_account():
    pass


@router.get(
    "/me/accounts/{account_id}/withdraws/list/", tags=["User-Me-Account-Withdraw"]
)
async def list_withdraw_in_account():
    pass


@router.get("/me/withdraws/{withdraw_id}/", tags=["User-Me-Account-Withdraw"])
async def retrieve_withdraw_in_account():
    pass


@router.delete("/me/accounts/{account_id}/delete/", tags=["User-Me-Account"])
async def delete_account_user_me():
    pass


@router.patch("/me/update/", tags=["User-Me"])
async def update_user_me():
    pass


@router.delete("/me/delete/", tags=["User-Me"])
async def delete_user_me():
    pass


@router.get("/me/loans/", tags=["User-Me-Loan"])
async def list_loans_user_me():
    pass


@router.get("/me/{account_id}/loans/list/", tags=["User-Me-Loan"])
async def list_loans_in_account_user_me():
    pass


@router.post("/me/{account_id}/loans/apply/", tags=["User-Me-Loan"])
async def apply_for_loan_in_account_user_me():
    pass


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
