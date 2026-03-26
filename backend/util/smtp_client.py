import smtplib
import mimetypes
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email.mime.application import MIMEApplication
from email import encoders
from email.utils import formatdate, make_msgid
from typing import Optional


def smtp_connect(host: str, port: int, user: str, password: str) -> smtplib.SMTP:
    smtp = smtplib.SMTP(host, port)
    smtp.ehlo()
    smtp.starttls()
    smtp.ehlo()
    smtp.login(user, password)
    return smtp


def smtp_disconnect(smtp: smtplib.SMTP):
    try:
        smtp.quit()
    except Exception:
        pass


def build_message(
    sender: str,
    to: list[str],
    subject: str,
    body_plain: str,
    body_html: Optional[str] = None,
    cc: Optional[list[str]] = None,
    bcc: Optional[list[str]] = None,
    attachments: Optional[list] = None,  # list of (filename, bytes, content_type)
    reply_to: Optional[str] = None,
    in_reply_to: Optional[str] = None,
    references: Optional[str] = None,
    message_id: Optional[str] = None,
) -> MIMEMultipart:

    msg = MIMEMultipart("mixed")
    msg["From"] = sender
    msg["To"] = ", ".join(to)
    msg["Date"] = formatdate(localtime=True)
    msg["Message-ID"] = message_id or make_msgid()
    msg["Subject"] = subject

    if cc:
        msg["Cc"] = ", ".join(cc)
    if bcc:
        msg["Bcc"] = ", ".join(bcc)
    if reply_to:
        msg["Reply-To"] = reply_to
    if in_reply_to:
        msg["In-Reply-To"] = in_reply_to
    if references:
        msg["References"] = references

    body_part = MIMEMultipart("alternative")
    body_part.attach(MIMEText(body_plain, "plain", "utf-8"))
    if body_html:
        body_part.attach(MIMEText(body_html, "html", "utf-8"))
    msg.attach(body_part)

    # attachement part by Claude
    for att in (attachments or []):
        filename, data, content_type = att
        maintype, subtype = (content_type or "application/octet-stream").split("/", 1)

        if maintype == "text":
            part = MIMEText(data.decode("utf-8", errors="replace"), subtype, "utf-8")
        elif maintype == "application":
            part = MIMEApplication(data, subtype)
        else:
            part = MIMEBase(maintype, subtype)
            part.set_payload(data)
            encoders.encode_base64(part)

        part.add_header("Content-Disposition", "attachment", filename=filename)
        msg.attach(part)

    return msg


def send_mail(
    smtp: smtplib.SMTP,
    sender: str,
    to: list[str],
    subject: str,
    body_plain: str,
    body_html: Optional[str] = None,
    cc: Optional[list[str]] = None,
    bcc: Optional[list[str]] = None,
    attachments: Optional[list] = None,
    in_reply_to: Optional[str] = None,
    references: Optional[str] = None,
) -> str:
    """returns the Message ID"""
    msg = build_message(
        sender=sender,
        to=to,
        subject=subject,
        body_plain=body_plain,
        body_html=body_html,
        cc=cc,
        bcc=bcc,
        attachments=attachments,
        in_reply_to=in_reply_to,
        references=references,
    )

    all_recipients = list(to) + (cc or []) + (bcc or [])
    smtp.sendmail(sender, all_recipients, msg.as_string())
    return msg["Message-ID"]


"""created by claude"""
def build_reply(
    original_subject: str,
    original_message_id: str,
    original_references: Optional[str],
    original_from: str,
    sender: str,
    to: list[str],
    body_plain: str,
    body_html: Optional[str] = None,
    cc: Optional[list[str]] = None,
    reply_all: bool = False,
) -> dict:
    """Returns kwargs ready to pass into send_mail()."""
    subject = original_subject
    if not subject.lower().startswith("re:"):
        subject = f"Re: {subject}"

    # Build references chain
    refs = original_references or ""
    if original_message_id:
        refs = f"{refs} {original_message_id}".strip()

    return {
        "to": to,
        "subject": subject,
        "body_plain": body_plain,
        "body_html": body_html,
        "cc": cc,
        "in_reply_to": original_message_id,
        "references": refs or None,
    }


def build_forward(
    original_subject: str,
    original_from: str,
    original_date: str,
    original_body_plain: str,
    to: list[str],
    body_plain: str,
    body_html: Optional[str] = None,
    cc: Optional[list[str]] = None,
    attachments: Optional[list] = None,
) -> dict:
    subject = original_subject
    if not subject.lower().startswith("fwd:") and not subject.lower().startswith("fw:"):
        subject = f"Fwd: {subject}"

    forward_quote = (
        f"\n\n-------- Forwarded Message --------\n"
        f"From: {original_from}\n"
        f"Date: {original_date}\n"
        f"Subject: {original_subject}\n\n"
        f"{original_body_plain}"
    )

    return {
        "to": to,
        "subject": subject,
        "body_plain": body_plain + forward_quote,
        "body_html": body_html,
        "cc": cc,
        "attachments": attachments,
    }