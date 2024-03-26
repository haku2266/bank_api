import smtplib
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from fastapi import HTTPException

from celery import Celery
from src.config import settings

app = Celery("tasks", broker="redis://localhost:6379")


@app.task
def send_email(email, validation_code, name):
    smtp_server = "smtp.gmail.com"
    port = 465
    password = settings.EMAIL_PASS

    sender_email = settings.EMAIL_USER
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
        <p style="text-align: center; margin: 0 auto;">This is your verification code<b> {validation_code}</b><br>
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
