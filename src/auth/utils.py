import bcrypt
from src.config import settings
import datetime
import jwt


# hashing password
def hash_password(password: str) -> bytes:
    salt = bcrypt.gensalt()

    password_bytes: bytes = password.encode()

    return bcrypt.hashpw(password_bytes, salt=salt)


# validating password
def validate_password(
    password: str,
    hashed_password: bytes,
) -> bool:
    return bcrypt.checkpw(
        password.encode(),
        hashed_password,
    )


def encode_jwt(
    payload: dict,
    private_key: str = settings.AUTH_JWT.private_key_path.read_text(),
    algorith: str = settings.AUTH_JWT.algorith,
    expire_minutes: int = settings.AUTH_JWT.access_token_exp_minutes,
):
    now = datetime.datetime.now(datetime.timezone.utc)

    expire = now + datetime.timedelta(minutes=expire_minutes)

    to_encode = payload.copy()

    to_encode.update(
        exp=expire,
        iat=now,
    )

    encoded = jwt.encode(
        to_encode,
        private_key,
        algorithm=algorith,
    )

    return encoded


def decode_jwt(
    jwt_token: str | bytes,
    public_key: str = settings.AUTH_JWT.public_key_path.read_text(),
    algorith: str = settings.AUTH_JWT.algorith,
):
    decoded = jwt.decode(jwt_token, public_key, algorithms=[algorith])

    return decoded
