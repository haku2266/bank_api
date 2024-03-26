from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi.security import (
    HTTPBearer,
    HTTPAuthorizationCredentials,
)
from jwt.exceptions import ExpiredSignatureError, DecodeError


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
    retrieve_validation_code,
    encode_jwt,
    decode_jwt,
)
from src.auth.crud import UserCRUD
from src.database import get_async_session
from src.auth.dependencies import retrieve_user_dependency, validate_user

from src.tasks.tasks import send_email

router = APIRouter(prefix="/user")

http_bearer = HTTPBearer()


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~JWT ISSUING~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
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


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~PERMISSIONS~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#


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


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ROUTERS~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
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
    await UserCRUD.delete_user(db=db, user=user)
    return None


@router.get("/me/", tags=["User-Me"])
async def retrieve_user_me(
    user: User = Depends(get_active_auth_user),
):
    return {"data": UserListSchema.model_validate(user, from_attributes=True)}


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
    await UserCRUD.delete_user(db=db, user=user)
    return None


@router.get("/me/loans/{loan_id}/", tags=["User-Me-Loan"])
async def retrieve_loan_user_me(
    user: User = Depends(get_active_auth_user),
):
    pass


@router.get("/me/loans/{loan_id}/compensations/list/", tags=["User-Me-Loan"])
async def list_loan_compensations_user_me(
    user: User = Depends(get_active_auth_user),
):
    pass


@router.post("/me/loans/{loan_id}/compensations/create/", tags=["User-Me-Loan"])
async def create_loan_compensation_user_me(
    user: User = Depends(get_active_auth_user),
):
    pass


@router.get("/me/compensations/{compensation_id}/detail/", tags=["User-Me-Loan"])
async def retrieve_compensations_user_me(
    user: User = Depends(get_active_auth_user),
):
    pass


@router.get("/me/{bank_id}/loan_types/list/", tags=["User-Me-Loan-Type"])
async def list_loan_types_user_me(
    user: User = Depends(get_active_auth_user),
):
    pass


@router.get("/me//loan_types/{loan_type_id}/detail/", tags=["User-Me-Loan-Type"])
async def retrieve_loan_types_user_me(
    user: User = Depends(get_active_auth_user),
):
    pass


@router.post("/activate/", tags=["User"])
async def activate_user(
    user_in: User = Depends(get_curr_auth_user),
    db: AsyncSession = Depends(get_async_session),
):
    email_in = user_in.email
    query = select(User).where(User.email == email_in)
    user = await db.scalar(query)
    if not user.is_active:

        validation_code = generate_validation_code()
        store_validation_code(
            email_in, validation_code, expiration_time=600
        )  # Set expiration time (in seconds)
        send_email.delay(email_in, validation_code, name=user.name)

        return {"message": f"Verification code has been sent to {email_in}"}

    else:
        raise HTTPException(
            status_code=404, detail={"message": "User is already active"}
        )

        # API endpoint to validate code


@router.post("/validate/activation_code/", tags=["User"])
async def validate_activation_code(
    code: str,
    user_in: User = Depends(get_curr_auth_user),
    db: AsyncSession = Depends(get_async_session),
):
    email_in = user_in.email
    query = select(User).where(User.email == email_in)
    user = await db.scalar(query)

    if not user:
        raise HTTPException(
            status_code=404, detail="User is not found. Check credentials"
        )

    if not user.is_active:
        stored_code = retrieve_validation_code(email_in)
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
            status_code=404, detail="User is already active"
        )
