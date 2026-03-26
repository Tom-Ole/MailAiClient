"""
Connection manager — creates IMAP / SMTP connections from session credentials.

Usage in routes:
    from util.connections import get_imap, get_smtp, require_auth

    @bp.route("/...")
    @require_auth
    def my_route():
        imap = get_imap()
        ...
"""

import functools
from flask import session, g, abort
from util.imap_client import imap_connect, imap_disconnect
from util.smtp_client import smtp_connect, smtp_disconnect


def require_auth(f):
    @functools.wraps(f)
    def decorated(*args, **kwargs):
        if "credentials" not in session:
            abort(401, description="Not authenticated")
        return f(*args, **kwargs)
    return decorated


def get_imap():
    """
    Returns a live IMAP connection for this request.
    Stored in Flask's `g` so it's created once per request and auto-closed.
    """
    if "imap" not in g:
        creds = session["credentials"]
        g.imap = imap_connect(
            host=creds["imap_host"],
            port=creds["imap_port"],
            user=creds["user"],
            password=creds["password"],
        )
    return g.imap


def get_smtp():
    """Returns a live SMTP connection for this request."""
    if "smtp" not in g:
        creds = session["credentials"]
        g.smtp = smtp_connect(
            host=creds["smtp_host"],
            port=creds["smtp_port"],
            user=creds["user"],
            password=creds["password"],
        )
    return g.smtp


def teardown_connections(exc):
    """Called automatically after each request to clean up connections."""
    imap = g.pop("imap", None)
    if imap is not None:
        imap_disconnect(imap)

    smtp = g.pop("smtp", None)
    if smtp is not None:
        smtp_disconnect(smtp)