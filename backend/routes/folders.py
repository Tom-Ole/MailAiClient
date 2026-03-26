import dataclasses
from flask import Blueprint, jsonify

from util.connections import get_imap, require_auth
from util.imap_client import list_folders

bp = Blueprint("folders", __name__, url_prefix="/folders")


@bp.get("/")
@require_auth
def get_folders():
    """
    GET /folders/
    Returns all selectable IMAP folders with unread + total counts.
    """
    imap = get_imap()
    folders = list_folders(imap)
    return jsonify({"folders": [dataclasses.asdict(f) for f in folders]})