from flask import Blueprint, request, jsonify, session

from util.connections import get_imap, get_smtp, require_auth
from util.imap_client import get_mail_by_uid
from util.smtp_client import send_mail, build_reply, build_forward

bp = Blueprint("compose", __name__, url_prefix="/mail")


def _parse_recipients(value) -> list[str]:
    """Accept a comma-separated string or a list."""
    if not value:
        return []
    if isinstance(value, list):
        return [v.strip() for v in value if v.strip()]
    return [v.strip() for v in str(value).split(",") if v.strip()]


def _parse_attachments(files) -> list[tuple[str, bytes, str]]:
    """Convert Flask file objects into (filename, bytes, content_type) tuples."""
    result = []
    for f in files:
        data = f.read()
        content_type = f.content_type or "application/octet-stream"
        result.append((f.filename, data, content_type))
    return result


@bp.post("/send")
@require_auth
def send():
    """
    POST /mail/send
    Multipart form OR JSON.

    Fields:
        to          (required)
        subject     (required)
        body_plain  (required)
        body_html   (optional)
        cc          (optional)
        bcc         (optional)
        files       (optional, multipart only)
    """
    if request.is_json:
        data = request.get_json(force=True)
        attachments = []
    else:
        data = request.form
        attachments = _parse_attachments(request.files.getlist("files"))

    to = _parse_recipients(data.get("to"))
    subject = data.get("subject", "").strip()
    body_plain = data.get("body_plain", "").strip()
    body_html = data.get("body_html") or None
    cc = _parse_recipients(data.get("cc"))
    bcc = _parse_recipients(data.get("bcc"))

    if not to:
        return jsonify({"error": "to is required"}), 400
    if not subject:
        return jsonify({"error": "subject is required"}), 400
    if not body_plain:
        return jsonify({"error": "body_plain is required"}), 400

    sender = session["credentials"]["user"]
    smtp = get_smtp()

    message_id = send_mail(
        smtp,
        sender=sender,
        to=to,
        subject=subject,
        body_plain=body_plain,
        body_html=body_html,
        cc=cc or None,
        bcc=bcc or None,
        attachments=attachments or None,
    )

    return jsonify({"message": "Sent", "message_id": message_id}), 201


@bp.post("/<uid>/reply")
@require_auth
def reply(uid):
    """
    POST /mail/<uid>/reply?folder=INBOX&reply_all=false
    Body: { "body_plain": "...", "body_html": "...", "cc": [...] }
    """
    folder = request.args.get("folder", "INBOX")
    reply_all = request.args.get("reply_all", "false").lower() == "true"

    if request.is_json:
        data = request.get_json(force=True)
        attachments = []
    else:
        data = request.form
        attachments = _parse_attachments(request.files.getlist("files"))

    body_plain = data.get("body_plain", "").strip()
    body_html = data.get("body_html") or None

    if not body_plain:
        return jsonify({"error": "body_plain is required"}), 400

    # Fetch original mail
    imap = get_imap()
    original = get_mail_by_uid(imap, uid=uid, folder=folder)
    if not original:
        return jsonify({"error": "Original mail not found"}), 404

    sender = session["credentials"]["user"]

    # Reply-to: the original sender (or all recipients if reply_all)
    reply_to_addresses = [original.sender]
    cc = None
    if reply_all:
        # Include original To/Cc minus ourselves
        all_recips = (
            [original.receiver, original.cc]
        )
        cc = [
            a.strip() for block in all_recips
            for a in block.split(",")
            if a.strip() and sender not in a
        ] or None

    extra_cc = _parse_recipients(data.get("cc")) or None

    kwargs = build_reply(
        original_subject=original.subject,
        original_message_id=original.message_id,
        original_references=original.references,
        original_from=original.sender,
        sender=sender,
        to=reply_to_addresses,
        body_plain=body_plain,
        body_html=body_html,
        cc=(cc or []) + (extra_cc or []) or None,
        reply_all=reply_all,
    )

    smtp = get_smtp()
    message_id = send_mail(smtp, sender=sender, attachments=attachments or None, **kwargs)
    return jsonify({"message": "Reply sent", "message_id": message_id}), 201




@bp.post("/<uid>/forward")
@require_auth
def forward(uid):
    """
    POST /mail/<uid>/forward?folder=INBOX
    Body: { "to": [...], "body_plain": "...", "body_html": "..." }
    """
    folder = request.args.get("folder", "INBOX")

    if request.is_json:
        data = request.get_json(force=True)
        new_attachments = []
    else:
        data = request.form
        new_attachments = _parse_attachments(request.files.getlist("files"))

    to = _parse_recipients(data.get("to"))
    cc = _parse_recipients(data.get("cc"))
    body_plain = data.get("body_plain", "").strip()
    body_html = data.get("body_html") or None

    if not to:
        return jsonify({"error": "to is required"}), 400

    # Fetch original
    imap = get_imap()
    original = get_mail_by_uid(imap, uid=uid, folder=folder)
    if not original:
        return jsonify({"error": "Original mail not found"}), 404

    sender = session["credentials"]["user"]

    kwargs = build_forward(
        original_subject=original.subject,
        original_from=original.sender,
        original_date=original.date,
        original_body_plain=original.body_plain,
        to=to,
        body_plain=body_plain or "",
        body_html=body_html,
        cc=cc or None,
        attachments=new_attachments or None,
    )

    smtp = get_smtp()
    message_id = send_mail(smtp, sender=sender, **kwargs)
    return jsonify({"message": "Forwarded", "message_id": message_id}), 201
