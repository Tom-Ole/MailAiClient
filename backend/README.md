# Email Web Client — Backend API
README create by AI


## Setup

```bash
pip install -r requirements.txt
```

### `.env`
```
SECRET_KEY=your-secret-key
# Optional defaults (can also be sent per-login)
IMAP_HOST=imap.gmx.net
SMTP_HOST=mail.gmx.net
```

### Run
```bash
python app.py
```

---

## Auth

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/auth/login` | Log in (starts session) |
| POST | `/auth/logout` | Clear session |
| GET | `/auth/me` | Current user info |

**Login body:**
```json
{
  "user": "me@example.com",
  "password": "secret",
  "imap_host": "imap.gmx.net",
  "smtp_host": "mail.gmx.net",
  "imap_port": 993,
  "smtp_port": 587
}
```

---

## Folders

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/folders/` | List all folders with unread + total counts |

---

## Mail

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/mail/` | List mails |
| GET | `/mail/search` | Search mails |
| GET | `/mail/<uid>` | Get full mail |
| PATCH | `/mail/<uid>` | Update flags |
| DELETE | `/mail/<uid>` | Delete mail |
| POST | `/mail/<uid>/move` | Move to folder |

### Query params (most endpoints)
- `folder` — IMAP folder name (default: `INBOX`)
- `page` — page number (default: `1`)
- `batchSize` — results per page (default: `50`)

### Search syntax (`/mail/search?q=...`)
```
from:alice             → filter by sender
to:bob                 → filter by recipient
subject:invoice        → filter by subject
body:meeting           → filter by body
unread / read          → flag filter
flagged                → flagged only
invoice unread         → bare terms match subject+from, combined with flags
```

### PATCH body
```json
{ "is_read": true, "is_flagged": false }
```

### Move body
```json
{ "source": "INBOX", "destination": "Archive" }
```

---

## Attachments

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/mail/<uid>/attachments` | List attachment metadata |
| GET | `/mail/<uid>/attachments/<filename>` | Download attachment |

---

## Compose

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/mail/send` | Send new email |
| POST | `/mail/<uid>/reply` | Reply to mail |
| POST | `/mail/<uid>/forward` | Forward mail |

All compose endpoints accept **JSON** or **multipart/form-data** (use multipart for attachments).

### Send body
```json
{
  "to": ["alice@example.com"],
  "subject": "Hello",
  "body_plain": "Hi there",
  "body_html": "<p>Hi there</p>",
  "cc": [],
  "bcc": []
}
```

### Reply body
```json
{
  "body_plain": "Thanks!",
  "body_html": "<p>Thanks!</p>"
}
```
Add `?reply_all=true` to reply to all.

### Forward body
```json
{
  "to": ["charlie@example.com"],
  "body_plain": "See below."
}
```

---

## Project structure

```
app.py                   ← app factory + blueprint registration
config.py                ← env config
models/
  dto.py                 ← MailDTO, MailSummaryDTO, FolderDTO, etc.
util/
  imap_client.py         ← all IMAP logic (fetch, search, flags, delete, move)
  smtp_client.py         ← all SMTP logic (send, reply, forward)
  connections.py         ← per-request connection manager + @require_auth
routes/
  auth.py                ← /auth/*
  mail.py                ← /mail/* (read, search, flags, delete, move, attachments)
  folders.py             ← /folders/
  compose.py             ← /mail/send, /mail/<uid>/reply|forward
```