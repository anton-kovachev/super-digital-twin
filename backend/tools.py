import traceback
import requests
import json
from pathlib import Path
from agents import function_tool
import smtplib
from email.message import EmailMessage
from config import (
    PUSHOVER_API_TOKEN,
    PUSHOVER_USER_KEY,
    PUSHOVER_API_URL,
    EMAIL_ADDRESS,
    EMAIL_SMTP_SERVER,
    EMAIL_APP_PASSWORD,
)


@function_tool
def push_message(message: str) -> str:
    """
    Record a contact request or email for follow-up by pushing it via Pushover notification API.
    Use this when a user wants to be contacted or leaves their email address.

    Args:
        message (str): The contact information (email, message, or request) to record.
    """
    # Here you can implement the logic to push a message using push notification API
    requests.post(
        PUSHOVER_API_URL,
        data={
            "message": message,
            "token": PUSHOVER_API_TOKEN,
            "user": PUSHOVER_USER_KEY,
        },
    )

    return f"Message pushed successfully: {message}"


@function_tool
def get_cv_pdf() -> str:
    """
    Provides a download link for the CV PDF file.
    Use this when the user asks for a resume, CV, or wants to download the PDF version.
    """
    pdf_path = Path(__file__).parent / "public" / "anton_kovachev_cv.pdf"

    if not pdf_path.exists():
        return "Sorry, the CV PDF file is not currently available."

    # Return the absolute path for Gradio to handle
    return f"FILE:{pdf_path.absolute()}"


@function_tool
def send_email(
    to_email: str,
    subject: str,
    text_body: str,
    html_body: str,
    attachments: list[str] | str | None = None,
) -> str:
    """
    Send an email to the specified recipient.
    Use this when a user wants to send an email by provided the email's content (text) and an optional attachment.

    Args:
        to_email (str): The recipient's email address.
        subject (str): The subject of the email.
        text_body (str): The body content of the email.
        html_body (str): The HTML content of the email.
        attachments (list[str], optional): List of file paths (strings) to attach to the email. Defaults to None. Always pass a list instance for attachments, even if it's empty.
    """

    if not EMAIL_ADDRESS or not EMAIL_SMTP_SERVER or not EMAIL_APP_PASSWORD:
        return "Email configuration is missing. Please check the environment configuration."

    msg = EmailMessage()
    msg["From"] = EMAIL_ADDRESS
    msg["To"] = EMAIL_ADDRESS
    msg["Subject"] = subject
    msg.set_content(text_body)
    msg.add_alternative(html_body, subtype="html")

    # Add attachments if provided
    if attachments:
        if isinstance(attachments, str):
            try:
                attachments = json.loads(attachments)
            except json.JSONDecodeError:
                attachments = []

        for attachment_path in attachments:
            file_path = Path(attachment_path)
            if file_path.exists():
                with open(file_path, "rb") as f:
                    file_data = f.read()
                    file_name = file_path.name
                    msg.add_attachment(
                        file_data,
                        maintype="application",
                        subtype="octet-stream",
                        filename=file_name,
                    )

    with smtplib.SMTP_SSL(EMAIL_SMTP_SERVER, 465) as server:
        try:
            # server.starttls()
            server.login(EMAIL_ADDRESS, EMAIL_APP_PASSWORD)
            server.send_message(msg)
        except Exception as e:
            traceback.print_exc()
            print(type(e), getattr(e, "errno", None))
            return f"Failed to send email: {e}"

    attachment_info = f" with {len(attachments)} attachment(s)" if attachments else ""
    return f"Email sent successfully to {to_email} with subject '{subject}'{attachment_info}"
