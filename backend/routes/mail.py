import dataclasses
import io
from flask import Blueprint, request, jsonify, send_file

from util.connections import get_imap, require_auth
from util.imap_client import (
    get_mail_list,
    get_mail_by_uid,
    get_attachments_meta,
    get_attachment_payload,
    search_mails,
    mark_read,
    mark_unread,
    mark_flagged,
    mark_unflagged,
    delete_mail,
    move_mail,
)

bp = Blueprint("mail", __name__, url_prefix="/mail")

def _dto_to_dict(obj):
    if dataclasses.is_dataclass(obj):
        return dataclasses.asdict(obj)
    if isinstance(obj, list):
        return [_dto_to_dict(i) for i in obj]
    return obj


@bp.get("/")
@require_auth
def list_mails():
    """
    GET /mail/?folder=INBOX&page=1&batchSize=50
    """
    folder = request.args.get("folder", "INBOX")
    page = int(request.args.get("page", 1))
    batch_size = int(request.args.get("batchSize", 50))

    imap = get_imap()
    mails = get_mail_list(imap, folder=folder, batch_size=batch_size, page=page)
    mails.reverse()  # Show newest first
    return jsonify({"mails": _dto_to_dict(mails), "page": page, "batchSize": batch_size})


@bp.get("/search")
@require_auth
def search():
    """
    GET /mail/search?q=...&folder=INBOX&page=1&batchSize=50

    Query syntax:
        from:alice subject:invoice unread
        plain terms match subject + from
    """
    q = request.args.get("q", "").strip()
    folder = request.args.get("folder", "INBOX")
    page = int(request.args.get("page", 1))
    batch_size = int(request.args.get("batchSize", 50))

    if not q:
        return jsonify({"error": "q is required"}), 400

    imap = get_imap()
    mails = search_mails(imap, query=q, folder=folder, batch_size=batch_size, page=page)
    return jsonify({"mails": _dto_to_dict(mails), "query": q, "folder": folder})

 

@bp.get("/<uid>")
@require_auth
def get_mail(uid):
    """GET /mail/<uid>?folder=INBOX"""
    folder = request.args.get("folder", "INBOX")
    imap = get_imap()
    mail = get_mail_by_uid(imap, uid=uid, folder=folder)

    # print content to file for debugging
    # with open("mail_content.txt", "w", encoding="utf-8") as f:
    #     f.write(mail.body)

    if not mail:
        return jsonify({"error": "Not found"}), 404
    return jsonify(_dto_to_dict(mail))


@bp.patch("/<uid>")
@require_auth
def update_mail(uid):
    """
    PATCH /mail/<uid>?folder=INBOX
    Body: { "is_read": true|false, "is_flagged": true|false }
    """
    folder = request.args.get("folder", "INBOX")
    data = request.get_json(force=True)
    imap = get_imap()

    if "is_read" in data:
        if data["is_read"]:
            mark_read(imap, uid, folder)
        else:
            mark_unread(imap, uid, folder)

    if "is_flagged" in data:
        if data["is_flagged"]:
            mark_flagged(imap, uid, folder)
        else:
            mark_unflagged(imap, uid, folder)

    return jsonify({"message": "Updated", "uid": uid})


@bp.delete("/<uid>")
@require_auth
def delete(uid):
    """DELETE /mail/<uid>?folder=INBOX"""
    folder = request.args.get("folder", "INBOX")
    imap = get_imap()
    delete_mail(imap, uid=uid, folder=folder)
    return jsonify({"message": "Deleted", "uid": uid})


@bp.post("/<uid>/move")
@require_auth
def move(uid):
    """
    POST /mail/<uid>/move
    Body: { "source": "INBOX", "destination": "Archive" }
    """
    data = request.get_json(force=True)
    source = data.get("source", "INBOX")
    destination = data.get("destination")
    if not destination:
        return jsonify({"error": "destination is required"}), 400

    imap = get_imap()
    move_mail(imap, uid=uid, source_folder=source, dest_folder=destination)
    return jsonify({"message": "Moved", "uid": uid, "to": destination})


@bp.get("/<uid>/attachments")
@require_auth
def list_attachments(uid):
    """GET /mail/<uid>/attachments?folder=INBOX"""
    folder = request.args.get("folder", "INBOX")
    imap = get_imap()
    attachments = get_attachments_meta(imap, uid=uid, folder=folder)
    return jsonify({"attachments": _dto_to_dict(attachments)})


@bp.get("/<uid>/attachments/<path:filename>")
@require_auth
def download_attachment(uid, filename):
    """GET /mail/<uid>/attachments/<filename>?folder=INBOX"""
    folder = request.args.get("folder", "INBOX")
    imap = get_imap()

    try:
        payload, content_type = get_attachment_payload(imap, uid=uid, filename=filename, folder=folder)
    except FileNotFoundError as e:
        return jsonify({"error": str(e)}), 404

    return send_file(
        io.BytesIO(payload),
        mimetype=content_type,
        as_attachment=True,
        download_name=filename,
    )