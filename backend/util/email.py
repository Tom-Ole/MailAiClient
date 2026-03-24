import imaplib
import email
from dotenv import load_dotenv
import os
from dataclasses import dataclass
from email import message_from_string, message_from_bytes
from email.policy import default
import mailparser

#['Return-Path', 'Authentication-Results', 'Received', 'DKIM-Signature', 'Received', 'Received', 'Content-Type', 'Date', 'From', 'Mime-Version', 'Message-ID', 'Subject', 'Reply-To', 'List-Unsubscribe', 'X-SG-EID', 'X-SG-ID', 'To', 'X-Entity-ID', 'Envelope-To', 'X-GMX-Antispam', 'X-Spam-Flag', 'X-UI-Filterresults']
@dataclass
class MailDTO:
    message_id: str
    sender: str
    receiver: str
    subject: str
    date: str
    timezone: str
    body: str
    bodyHtml: str
    bodyPlain: str
    

def parse_address(header_value):
            """Return a readable string from a raw header value"""
            if not header_value:
                return ""
            from email.utils import getaddresses
            addresses = getaddresses([header_value])
            return ", ".join(f"{name} <{email}>" if name else email for name, email in addresses)

def mail_init(host: str) -> imaplib.IMAP4_SSL:
    # connect to email
    imap = imaplib.IMAP4_SSL(host)

    load_dotenv()
    email_user = os.getenv("EMAIL_USER")
    email_pass = os.getenv("EMAIL_PASS")

    imap.login(email_user, email_pass)

    imap.select("INBOX")

    return imap

def get_mails(imap: imaplib.IMAP4_SSL, batch_size: int, page: int):
    status, messages = imap.search(None, "ALL")

    if status != "OK" or not messages or not messages[0]:
        return []

    mail_ids = messages[0].split()
    mail_ids.reverse()

    mails = []
    
    prev_idx = batch_size * (page - 1)
    idx = batch_size * page


    for mail_id in mail_ids[prev_idx:idx]:
        status, msg_data = imap.fetch(mail_id, "(RFC822)")

        if status != "OK":
            raise imaplib.IMAP4.error(f"Failed {mail_id}")

        raw_email = msg_data[0][1]
        msg = email.message_from_bytes(raw_email)

        mail = mailparser.parse_from_bytes(raw_email)


        sub = message_from_string(f"Subject: {msg.get("Subject")}", policy=default)


        sender = parse_address(mail.mail.get("from"))
        receiver = parse_address(mail.mail.get("to"))
        message_id = (mail.mail.get("message-id") or "").strip()

        mails.append(MailDTO(
            message_id=message_id,
            sender=msg.get("From"),
            receiver=receiver,
            subject=sub.get("Subject"),
            date=mail.date.strftime("%Y-%m-%d %H:%M:%S"),
            timezone=mail.timezone,
            body=mail.body,
            bodyHtml=mail.text_html[0] if mail.text_html else "",
            bodyPlain=mail.text_plain[0] if mail.text_plain else ""
            ))
    
    return mails