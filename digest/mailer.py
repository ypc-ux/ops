"""Send the digest email. Same pattern as ascent-ascent's submit.js smtpSend():
TLS to smtp.gmail.com:465 with an app password. Zero third-party deps.
"""
import os
import smtplib
from email.message import EmailMessage


class MailerConfigError(RuntimeError):
    pass


def send(subject: str, body: str, to: str | None = None) -> None:
    user = os.environ.get("GMAIL_USER")
    password = os.environ.get("GMAIL_APP_PASSWORD")
    recipient = to or os.environ.get("NOTIFY_TO")

    if not user or not password or not recipient:
        raise MailerConfigError(
            "GMAIL_USER, GMAIL_APP_PASSWORD, and NOTIFY_TO (or --to) are all required to send"
        )

    msg = EmailMessage()
    msg["From"] = user
    msg["To"] = recipient
    msg["Subject"] = subject
    msg.set_content(body)

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login(user, password)
        smtp.send_message(msg)
