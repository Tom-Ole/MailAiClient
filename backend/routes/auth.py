from flask import Blueprint, request, session, jsonify
from util.imap_client import imap_connect, imap_disconnect
from util.smtp_client import smtp_connect, smtp_disconnect

bp = Blueprint("auth", __name__, url_prefix="/auth")


@bp.post("/login")
def login():
    """
    POST /auth/login
    Body (JSON):
    {
        "user": "me@example.com",
        "password": "secret",
        "imap_host": "imap.gmx.net",
        "imap_port": 993,          // optional, default 993
        "smtp_host": "mail.gmx.net",
        "smtp_port": 587            // optional, default 587
    }
    """
    data = request.get_json(force=True)

    user = data.get("user", "").strip()
    password = data.get("password", "")
    imap_host = data.get("imap_host", "").strip()
    smtp_host = data.get("smtp_host", "").strip()
    imap_port = int(data.get("imap_port", 993))
    smtp_port = int(data.get("smtp_port", 587))

    if not user or not password or not imap_host or not smtp_host:
        return jsonify({"error": "user, password, imap_host and smtp_host are required"}), 400

    try:
        imap = imap_connect(imap_host, imap_port, user, password)
        imap_disconnect(imap)
    except Exception as e:
        return jsonify({"error": f"IMAP login failed: {str(e)}"}), 401

    try:
        smtp = smtp_connect(smtp_host, smtp_port, user, password)
        smtp_disconnect(smtp)
    except Exception as e:
        return jsonify({"error": f"SMTP login failed: {str(e)}"}), 401

    session.clear()
    session["credentials"] = {
        "user": user,
        "password": password,
        "imap_host": imap_host,
        "imap_port": imap_port,
        "smtp_host": smtp_host,
        "smtp_port": smtp_port,
    }

    return jsonify({
        "message": "Logged in successfully",
        "user": user,
        "imap_host": imap_host,
        "smtp_host": smtp_host,
    })


@bp.post("/logout")
def logout():
    session.clear()
    return jsonify({"message": "Logged out"})


@bp.get("/me")
def me():
    creds = session.get("credentials")
    if not creds:
        return jsonify({"authenticated": False}), 401
    return jsonify({
        "authenticated": True,
        "user": creds["user"],
        "imap_host": creds["imap_host"],
        "smtp_host": creds["smtp_host"],
    })