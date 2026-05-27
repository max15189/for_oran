import io
import os
import datetime
import logging
import hashlib
import hmac

import openpyxl
from dotenv import load_dotenv
from flask import Flask, abort, render_template, request, send_file, Response
from functools import wraps

from models import Guest, Session

load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger(__name__)

app = Flask(__name__)

ADMIN_PASSWORD      = os.getenv("ADMIN_PASSWORD", "admin123")
INVITATION_MESSAGE  = os.getenv("INVITATION_MESSAGE", "You are invited!")
WEBHOOK_VERIFY_TOKEN = os.getenv("WEBHOOK_VERIFY_TOKEN", "")
WHATSAPP_APP_SECRET  = os.getenv("WHATSAPP_APP_SECRET", "")   # optional, for signature check

REPLY_MAP = {"1": "yes", "2": "no", "3": "maybe"}


# ── admin auth ────────────────────────────────────────────────────────────────

def require_admin(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or auth.password != ADMIN_PASSWORD:
            return Response("Login required", 401, {"WWW-Authenticate": 'Basic realm="Admin"'})
        return f(*args, **kwargs)
    return decorated


# ── webhook ───────────────────────────────────────────────────────────────────

@app.route("/webhook", methods=["GET"])
def webhook_verify():
    """Meta calls this once when you register the webhook URL."""
    if (request.args.get("hub.mode") == "subscribe"
            and request.args.get("hub.verify_token") == WEBHOOK_VERIFY_TOKEN):
        return request.args.get("hub.challenge", ""), 200
    return "Forbidden", 403


@app.route("/webhook", methods=["POST"])
def webhook_receive():
    """Meta calls this every time a guest replies."""
    # Optional signature verification
    if WHATSAPP_APP_SECRET:
        sig = request.headers.get("X-Hub-Signature-256", "")
        expected = "sha256=" + hmac.new(
            WHATSAPP_APP_SECRET.encode(), request.data, hashlib.sha256
        ).hexdigest()
        if not hmac.compare_digest(sig, expected):
            return "Forbidden", 403

    data = request.get_json(silent=True) or {}
    try:
        for entry in data.get("entry", []):
            for change in entry.get("changes", []):
                for msg in change.get("value", {}).get("messages", []):
                    if msg.get("type") == "text":
                        _handle_reply(
                            phone=msg["from"],
                            text=msg["text"]["body"].strip(),
                        )
    except Exception as exc:
        log.error("Webhook error: %s", exc)

    # Always 200 — Meta retries on anything else
    return "OK", 200


def _handle_reply(phone: str, text: str):
    response = REPLY_MAP.get(text)
    if not response:
        log.info("Ignored unrecognized reply '%s' from %s", text, phone)
        return
    db = Session()
    guest = db.query(Guest).filter_by(phone=phone).first()
    if guest:
        guest.response = response
        guest.responded_at = datetime.datetime.utcnow()
        db.commit()
        log.info("Saved response '%s' from %s (%s)", response, guest.name, phone)
    else:
        log.warning("Reply from unknown number: %s", phone)
    db.close()


# ── admin dashboard ───────────────────────────────────────────────────────────

@app.route("/admin")
@require_admin
def admin():
    db = Session()
    guests = db.query(Guest).order_by(Guest.name).all()
    stats = {
        "total":   len(guests),
        "yes":     sum(1 for g in guests if g.response == "yes"),
        "no":      sum(1 for g in guests if g.response == "no"),
        "maybe":   sum(1 for g in guests if g.response == "maybe"),
        "pending": sum(1 for g in guests if not g.response),
    }
    result = render_template("admin.html", guests=guests, stats=stats)
    db.close()
    return result


@app.route("/admin/export")
@require_admin
def export_excel():
    db = Session()
    guests = db.query(Guest).order_by(Guest.name).all()
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "RSVP Responses"
    ws.append(["Name", "Phone", "Response", "Responded At", "Invited At"])
    for g in guests:
        ws.append([
            g.name,
            g.phone,
            g.response or "Pending",
            str(g.responded_at) if g.responded_at else "",
            str(g.invited_at)   if g.invited_at   else "",
        ])
    db.close()
    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    return send_file(
        buf,
        download_name="rsvp_responses.xlsx",
        as_attachment=True,
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
