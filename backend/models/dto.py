from dataclasses import dataclass, field
from typing import Optional


@dataclass
class MailDTO:
    uid: str
    message_id: str
    sender: str
    receiver: str
    cc: str
    bcc: str
    subject: str
    date: str
    timezone: str
    is_read: bool
    is_flagged: bool
    has_attachments: bool
    folder: str
    body: str
    body_html: str
    body_plain: str
    in_reply_to: Optional[str] = None
    references: Optional[str] = None


@dataclass
class MailSummaryDTO:
    """Lightweight version for listing"""
    uid: str
    message_id: str
    sender: str
    receiver: str
    subject: str
    date: str
    is_read: bool
    is_flagged: bool
    has_attachments: bool
    folder: str


@dataclass
class AttachmentDTO:
    filename: str
    content_type: str
    size: int


@dataclass
class FolderDTO:
    name: str
    display_name: str
    flags: list
    delimiter: str
    unread_count: Optional[int] = None
    total_count: Optional[int] = None


@dataclass
class SendMailDTO:
    to: list
    subject: str
    body_plain: str
    body_html: Optional[str] = None
    cc: Optional[list] = None
    bcc: Optional[list] = None
    attachments: Optional[list] = None
    reply_to_message_id: Optional[str] = None
    references: Optional[str] = None
    in_reply_to: Optional[str] = None