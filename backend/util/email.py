import imaplib
import email
from dotenv import load_dotenv
import os
from dataclasses import dataclass

#['Return-Path', 'Authentication-Results', 'Received', 'DKIM-Signature', 'Received', 'Received', 'Content-Type', 'Date', 'From', 'Mime-Version', 'Message-ID', 'Subject', 'Reply-To', 'List-Unsubscribe', 'X-SG-EID', 'X-SG-ID', 'To', 'X-Entity-ID', 'Envelope-To', 'X-GMX-Antispam', 'X-Spam-Flag', 'X-UI-Filterresults']
@dataclass
class MailDTO:
    message_id: str
    sender: str
    receiver: str
    subject: str
    date: str
    body: str
    
def get_body(msg):
        for part in msg.walk():
            if part.get_content_type() == "text/plain":
                return part.get_payload(decode=True).decode(errors="ignore")
        return ""

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


        
        mails.append(MailDTO(
            message_id=msg.get("Message-Id"),
            sender=msg.get("From"),
            receiver=msg.get("Received"),
            subject=msg.get("Subject"),
            date=msg.get("Date"),
            body=get_body(msg),
            ))
    
    return mails