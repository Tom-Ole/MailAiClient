from email.header import decode_header
import imaplib
import email
import mailparser
from email import message_from_string
from email.policy import default as email_default_policy
from email.utils import getaddresses
from typing import Optional

from models.dto import MailDTO, MailSummaryDTO, AttachmentDTO, FolderDTO


def imap_connect(host: str, port: int, user: str, password: str) -> imaplib.IMAP4_SSL:
    imap = imaplib.IMAP4_SSL(host, port)
    imap.login(user, password)
    return imap


def imap_disconnect(imap: imaplib.IMAP4_SSL):
    try:
        imap.logout()
    except Exception:
        pass


def decode_mime(value: str) -> str:
    if not value:
        return ""

    parts = decode_header(value)
    result = ""

    for part, enc in parts:
        if isinstance(part, bytes):
            result += part.decode(enc or "utf-8", errors="replace")
        else:
            result += part

    return result

def parse_address(header_value) -> str:
    if not header_value:
        return ""

    # --- CASE 1: mailparser gives list ---
    if isinstance(header_value, list):
        cleaned = []
        for item in header_value:
            if isinstance(item, tuple) and len(item) == 2:
                name, addr = item
                name = (name or "").strip()
                addr = (addr or "").strip()

                if not name and not addr:
                    continue

                if name:
                    cleaned.append(f"{name} <{addr}>")
                else:
                    cleaned.append(addr)

        return ", ".join(cleaned)

    # --- CASE 2: normal string header ---
    decoded_parts = decode_header(header_value)
    decoded = ""
    for part, enc in decoded_parts:
        if isinstance(part, bytes):
            decoded += part.decode(enc or "utf-8", errors="replace")
        else:
            decoded += part

    addresses = getaddresses([decoded])

    cleaned = []
    for name, addr in addresses:
        name = name.strip()
        addr = addr.strip()

        if not name and not addr:
            continue

        if name:
            cleaned.append(f"{name} <{addr}>")
        else:
            cleaned.append(addr)

    return ", ".join(cleaned)

def list_folders(imap: imaplib.IMAP4_SSL) -> list[FolderDTO]:
    status, folder_list = imap.list()
    folders = []
    if status != "OK":
        return folders

    for item in folder_list:
        if isinstance(item, bytes):
            item = item.decode()

        # Parse: (\HasNoChildren) "/" "INBOX" - created by claude
        parts = item.split('"')
        if len(parts) >= 3:
            flags_part = parts[0].strip().strip("()")
            delimiter = parts[1]
            name = parts[2].strip().strip('"').strip()
        else:
            tokens = item.rsplit(" ", 1)
            flags_part = ""
            delimiter = "/"
            name = tokens[-1].strip().strip('"')

        flags = [f.strip() for f in flags_part.split("\\") if f.strip()]
        display_name = name.split(delimiter)[-1] if delimiter in name else name

        if "Noselect" in flags:
            continue

        unread, total = _get_folder_counts(imap, name)

        folders.append(FolderDTO(
            name=name,
            display_name=display_name,
            flags=flags,
            delimiter=delimiter,
            unread_count=unread,
            total_count=total,
        ))

    return folders


def _get_folder_counts(imap: imaplib.IMAP4_SSL, folder: str) -> tuple[int, int]:
    try:
        status, data = imap.select(f'"{folder}"', readonly=True)
        if status != "OK":
            return 0, 0
        total = int(data[0]) if data[0] else 0

        status, unseen = imap.search(None, "UNSEEN")
        unread = len(unseen[0].split()) if status == "OK" and unseen[0] else 0
        return unread, total
    except Exception:
        return 0, 0


def _select_folder(imap: imaplib.IMAP4_SSL, folder: str, readonly: bool = False):
    status, data = imap.select(f'"{folder}"', readonly=readonly)
    if status != "OK":
        raise ValueError(f"Cannot select folder: {folder}")
    return data


def get_mail_list(
    imap: imaplib.IMAP4_SSL,
    folder: str = "INBOX",
    batch_size: int = 50,
    page: int = 1,
) -> list[MailSummaryDTO]:
    _select_folder(imap, folder, readonly=True)

    status, messages = imap.uid("search", None, "ALL")
    if status != "OK" or not messages or not messages[0]:
        return []

    uid_list = messages[0].split()
    uid_list.reverse()  # newest first

    start = batch_size * (page - 1)
    end = batch_size * page
    page_uids = uid_list[start:end]

    if not page_uids:
        return []

    uid_str = b",".join(page_uids)
    status, msg_data = imap.uid("fetch", uid_str, "(FLAGS RFC822.HEADER)")
    if status != "OK":
        return []

    results = []
    i = 0
    while i < len(msg_data):
        item = msg_data[i]
        if not isinstance(item, tuple):
            i += 1
            continue

        meta, raw_header = item
        uid = _extract_uid(meta.decode() if isinstance(meta, bytes) else meta)
        flags = _extract_flags(meta.decode() if isinstance(meta, bytes) else meta)

        msg = email.message_from_bytes(raw_header)
        subject_obj = message_from_string(
            f"Subject: {msg.get('Subject', '')}", policy=email_default_policy
        )

        has_attachments = _header_indicates_attachments(msg)

        results.append(MailSummaryDTO(
            uid=uid,
            message_id=(msg.get("Message-ID") or "").strip(),
            sender=parse_address(msg.get("From", "")),
            receiver=parse_address(msg.get("To", "")),
            subject=subject_obj.get("Subject") or "(no subject)",
            date=msg.get("Date", ""),
            is_read="\\Seen" in flags,
            is_flagged="\\Flagged" in flags,
            has_attachments=has_attachments,
            folder=folder,
        ))
        i += 1

    return results


def get_mail_by_uid(
    imap: imaplib.IMAP4_SSL,
    uid: str,
    folder: str = "INBOX",
) -> Optional[MailDTO]:
    _select_folder(imap, folder, readonly=True)

    status, msg_data = imap.uid("fetch", uid, "(FLAGS RFC822)")
    if status != "OK" or not msg_data or not msg_data[0]:
        return None

    imap.uid("store", uid, "+FLAGS", "\\Seen")

    meta, raw_email = msg_data[0]
    flags = _extract_flags(meta.decode() if isinstance(meta, bytes) else meta)

    mail = mailparser.parse_from_bytes(raw_email)
    msg = email.message_from_bytes(raw_email)

    subject_obj = message_from_string(
        f"Subject: {msg.get('Subject', '')}", policy=email_default_policy
    )

    has_attachments = bool(mail.attachments)

    return MailDTO(
        uid=uid,
        message_id=(mail.mail.get("message-id") or "").strip(),
        sender=parse_address(mail.mail.get("from") or msg.get("From", "")),
        receiver=parse_address(mail.mail.get("to") or msg.get("To", "")),
        cc=parse_address(mail.mail.get("cc") or msg.get("Cc", "")),
        bcc=parse_address(mail.mail.get("bcc") or msg.get("Bcc", "")),
        subject=subject_obj.get("Subject") or "(no subject)",
        date=mail.date.strftime("%Y-%m-%d %H:%M:%S") if mail.date else msg.get("Date", ""),
        timezone=str(mail.timezone) if hasattr(mail, "timezone") else "",
        is_read="\\Seen" in flags,
        is_flagged="\\Flagged" in flags,
        has_attachments=has_attachments,
        folder=folder,
        body=mail.body or "",
        body_html=mail.text_html[0] if mail.text_html else "",
        body_plain=mail.text_plain[0] if mail.text_plain else "",
        in_reply_to=(msg.get("In-Reply-To") or "").strip() or None,
        references=(msg.get("References") or "").strip() or None,
    )


def get_attachments_meta(
    imap: imaplib.IMAP4_SSL,
    uid: str,
    folder: str = "INBOX",
) -> list[AttachmentDTO]:
    _select_folder(imap, folder, readonly=True)
    status, msg_data = imap.uid("fetch", uid, "(RFC822)")
    if status != "OK" or not msg_data or not msg_data[0]:
        return []

    raw_email = msg_data[0][1]
    mail = mailparser.parse_from_bytes(raw_email)

    return [
        AttachmentDTO(
            filename=att.get("filename", "attachment"),
            content_type=att.get("mail_content_type", "application/octet-stream"),
            size=len(att.get("payload", b"")),
        )
        for att in mail.attachments
    ]


def get_attachment_payload(
    imap: imaplib.IMAP4_SSL,
    uid: str,
    filename: str,
    folder: str = "INBOX",
) -> tuple[bytes, str]:
    """Returns (bytes, content_type)"""
    _select_folder(imap, folder, readonly=True)
    status, msg_data = imap.uid("fetch", uid, "(RFC822)")
    if status != "OK" or not msg_data or not msg_data[0]:
        raise FileNotFoundError("Message not found")

    raw_email = msg_data[0][1]
    mail = mailparser.parse_from_bytes(raw_email)

    for att in mail.attachments:
        if att.get("filename") == filename:
            payload = att.get("payload", b"")
            if isinstance(payload, str):
                import base64
                payload = base64.b64decode(payload)
            return payload, att.get("mail_content_type", "application/octet-stream")

    raise FileNotFoundError(f"Attachment '{filename}' not found")


"""created by claude"""
def search_mails(
    imap: imaplib.IMAP4_SSL,
    query: str,
    folder: str = "INBOX",
    batch_size: int = 50,
    page: int = 1,
) -> list[MailSummaryDTO]:
    _select_folder(imap, folder, readonly=True)

    criteria = _build_search_criteria(query)

    status, messages = imap.uid("search", None, criteria)
    if status != "OK" or not messages or not messages[0]:
        return []

    uid_list = messages[0].split()
    uid_list.reverse()

    start = batch_size * (page - 1)
    end = batch_size * page
    page_uids = uid_list[start:end]
    if not page_uids:
        return []

    uid_str = b",".join(page_uids)
    status, msg_data = imap.uid("fetch", uid_str, "(FLAGS RFC822.HEADER)")
    if status != "OK":
        return []

    results = []
    for item in msg_data:
        if not isinstance(item, tuple):
            continue

        meta, raw_header = item
        uid = _extract_uid(meta.decode() if isinstance(meta, bytes) else meta)
        flags = _extract_flags(meta.decode() if isinstance(meta, bytes) else meta)

        msg = email.message_from_bytes(raw_header)
        subject_obj = message_from_string(
            f"Subject: {msg.get('Subject', '')}", policy=email_default_policy
        )

        results.append(MailSummaryDTO(
            uid=uid,
            message_id=(msg.get("Message-ID") or "").strip(),
            sender=parse_address(msg.get("From", "")),
            receiver=parse_address(msg.get("To", "")),
            subject=subject_obj.get("Subject") or "(no subject)",
            date=msg.get("Date", ""),
            is_read="\\Seen" in flags,
            is_flagged="\\Flagged" in flags,
            has_attachments=_header_indicates_attachments(msg),
            folder=folder,
        ))

    return results


def _build_search_criteria(query: str) -> str:
    """
    Supports prefixes: from:, to:, subject:, body:
    Bare terms search subject + from.
    ~ created by Claude
    """
    parts = []
    tokens = query.strip().split()
    bare_terms = []

    for token in tokens:
        lower = token.lower()
        if lower.startswith("from:"):
            val = token[5:]
            parts.append(f'FROM "{val}"')
        elif lower.startswith("to:"):
            val = token[3:]
            parts.append(f'TO "{val}"')
        elif lower.startswith("subject:"):
            val = token[8:]
            parts.append(f'SUBJECT "{val}"')
        elif lower.startswith("body:"):
            val = token[5:]
            parts.append(f'BODY "{val}"')
        elif lower == "unread":
            parts.append("UNSEEN")
        elif lower == "read":
            parts.append("SEEN")
        elif lower == "flagged":
            parts.append("FLAGGED")
        else:
            bare_terms.append(token)

    for term in bare_terms:
        parts.append(f'OR SUBJECT "{term}" FROM "{term}"')

    return " ".join(parts) if parts else "ALL"


def set_flag(
    imap: imaplib.IMAP4_SSL,
    uid: str,
    flag: str,
    value: bool,
    folder: str = "INBOX",
):
    _select_folder(imap, folder, readonly=False)
    op = "+FLAGS" if value else "-FLAGS"
    imap.uid("store", uid, op, flag)


def mark_read(imap, uid, folder="INBOX"):
    set_flag(imap, uid, "\\Seen", True, folder)


def mark_unread(imap, uid, folder="INBOX"):
    set_flag(imap, uid, "\\Seen", False, folder)


def mark_flagged(imap, uid, folder="INBOX"):
    set_flag(imap, uid, "\\Flagged", True, folder)


def mark_unflagged(imap, uid, folder="INBOX"):
    set_flag(imap, uid, "\\Flagged", False, folder)


def delete_mail(imap: imaplib.IMAP4_SSL, uid: str, folder: str = "INBOX"):
    _select_folder(imap, folder, readonly=False)
    imap.uid("store", uid, "+FLAGS", "\\Deleted")
    imap.expunge()


def move_mail(
    imap: imaplib.IMAP4_SSL,
    uid: str,
    source_folder: str,
    dest_folder: str,
):
    _select_folder(imap, source_folder, readonly=False)

    try:
        status, _ = imap.uid("move", uid, f'"{dest_folder}"')
        if status == "OK":
            return
    except (imaplib.IMAP4.error, AttributeError):
        pass

    # Fallback
    status, _ = imap.uid("copy", uid, f'"{dest_folder}"')
    if status != "OK":
        raise ValueError(f"Failed to copy to {dest_folder}")

    imap.uid("store", uid, "+FLAGS", "\\Deleted")
    imap.expunge()


def _extract_uid(meta_str: str) -> str:
    import re
    match = re.search(r"UID\s+(\d+)", meta_str, re.IGNORECASE)
    return match.group(1) if match else ""


def _extract_flags(meta_str: str) -> list[str]:
    import re
    match = re.search(r"FLAGS\s+\(([^)]*)\)", meta_str, re.IGNORECASE)
    if not match:
        return []
    return match.group(1).split()


def _header_indicates_attachments(msg) -> bool:
    for part in msg.walk():
        disposition = part.get_content_disposition()
        if disposition and disposition.lower() in ("attachment", "inline"):
            if part.get_filename():
                return True
    return False