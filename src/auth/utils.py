from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from fastapi import HTTPException

import bcrypt
from src.config import settings
import datetime
import jwt


import random
import string
import smtplib
import ssl
import redis

redis_client = redis.StrictRedis(host="localhost", port=6379, db=0)


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


def generate_validation_code():
    return "".join(random.choices(string.ascii_uppercase + string.digits, k=6))


def send_email(email, validation_code, name):
    smtp_server = "smtp.gmail.com"
    port = 465
    password = "cqhvezlrvpgcbsnu"

    sender_email = "hamidakhtamov1@gmail.com"
    receiver_email = email

    message = MIMEMultipart("alternative")
    message["Subject"] = "Verification Code"
    message["From"] = sender_email
    message["To"] = receiver_email

    # Create the plain-text and HTML version of your message
    text = """\
    Hi,
    We are really happy that you become the member of your family!"""
    html = f"""\
    <html>
      <body>
        <h2 style="text-align: center; margin: 0 auto;">Hi, {name}!</h2>
        <h4 style="text-align: center; margin: 0 auto;">We are really happy that you become the member of your family!?</h4>
        <p style="text-align: center; margin: 0 auto;">This is your verification code: <b>{validation_code}</b><br>
        You have <b>10</b> minutes to verify your account, then the code will be invalid.
        </p>
      </body>
    </html>
    """

    # Turn these into plain/html MIMEText objects
    part1 = MIMEText(text, "plain")
    part2 = MIMEText(html, "html")

    # Add HTML/plain-text parts to MIMEMultipart message
    # The email client will try to render the last part first
    message.attach(part1)
    message.attach(part2)

    try:
        # Create secure connection with server and send email
        context = ssl.create_default_context()
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
            server.login(sender_email, password)
            server.sendmail(sender_email, receiver_email, message.as_string())
    except TimeoutError:
        raise HTTPException(status_code=400, detail="Inconsistent network")


# Store validation code in Redis with expiration time
def store_validation_code(email, validation_code, expiration_time):
    redis_client.setex(email, expiration_time, validation_code)


# Retrieve validation code from Redis
def retrieve_validation_code(email):
    return redis_client.get(email)


