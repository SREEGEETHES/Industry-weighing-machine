"""
Sends the weekly Excel report over real SMTP (Gmail App Password or any
other SMTP provider). No mock/console-print fallback - if SMTP credentials
are missing or wrong, this raises so the failure is visible and logged,
not silently skipped.
"""
import smtplib
import ssl
from email.message import EmailMessage

from app.config import SMTP_HOST, SMTP_PORT, SMTP_USERNAME, SMTP_PASSWORD, SMTP_FROM_NAME


class EmailSendError(Exception):
    pass


def send_weekly_report_email(recipients: list[str], filepath: str,
                              period_start_str: str, period_end_str: str,
                              summary_lines: list[str]) -> None:
    if not SMTP_USERNAME or not SMTP_PASSWORD:
        raise EmailSendError(
            "SMTP_USERNAME / SMTP_PASSWORD not configured. Set them in "
            "backend/.env before the weekly report job can send email."
        )
    if not recipients:
        raise EmailSendError("No active email recipients configured in the admin panel.")

    msg = EmailMessage()
    msg["Subject"] = f"Weigh & Print Audit Report - {period_start_str} to {period_end_str}"
    msg["From"] = f"{SMTP_FROM_NAME} <{SMTP_USERNAME}>"
    msg["To"] = ", ".join(recipients)

    body = (
        f"Weekly Weigh & Print Audit Report\n"
        f"Period: {period_start_str} to {period_end_str}\n\n"
        + "\n".join(summary_lines)
        + "\n\nFull detail attached as Excel.\n"
        "This is an automated message from the Industrial Weigh-Print-Audit System."
    )
    msg.set_content(body)

    with open(filepath, "rb") as f:
        file_data = f.read()
    msg.add_attachment(
        file_data,
        maintype="application",
        subtype="vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        filename=filepath.split("/")[-1],
    )

    context = ssl.create_default_context()
    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=15) as server:
            server.starttls(context=context)
            server.login(SMTP_USERNAME, SMTP_PASSWORD)
            server.send_message(msg)
    except (smtplib.SMTPException, OSError) as e:
        # OSError covers network-level failures (DNS, connection refused,
        # firewall blocking outbound SMTP) that smtplib doesn't wrap in
        # SMTPException - both must surface as a clean, actionable error
        # rather than an unhandled 500.
        raise EmailSendError(f"Failed to send report email: {e}") from e
