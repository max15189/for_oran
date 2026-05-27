import io
import os
import datetime
import logging

import openpyxl
from dotenv import load_dotenv
from flask import Flask, render_template, request, send_file, Response
from functools import wraps
from twilio.twiml.messaging_response import MessagingResponse
from twilio.request_validator import RequestValidator

from models import Guest, Session

load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger(__name__)

app = Flask(__name__)

ADMIN_PASSWORD     = os.getenv("ADMIN_PASSWORD", "admin123")
TWILIO_AUTH_TOKEN  = os.getenv("TWILIO_AUTH_TOKEN", "")

REPLY_MAP = {
    "1": ("yes",   "We're so happy you'll be joining us! See you there 🎉"),
    "2": ("no",    "We'll miss you! Thank you for letting us know 💌"),
    "3": ("maybe", "No worries, let us know whenever you decide 😊"),
}
UNKNOWN_REPLY = "Please reply with 1 (Yes, I'll be there), 2 (Sadly I can't), or 3 (Not sure yet)."


# ── admin auth ─────────────────────────────────────────────────────────────────

def require_admin(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or auth.password != ADMIN_PASSWORD:
            return Response("Login required", 401, {"WWW-Authenticate": 'Basic realm="Admin"'})
        return f(*args, **kwargs)
    return decorated


# ── webhook ────────────────────────────────────────────────────────────────────

@app.route("/webhook", methods=["POST"])
def webhook_receive():
    # Validate the request came from Twilio
    if TWILIO_AUTH_TOKEN:
        validator = RequestValidator(TWILIO_AUTH_TOKEN)
        if not validator.validate(request.url, request.form,
                                  request.headers.get("X-Twilio-Signature", "")):
            return Response("Forbidden", 403)

    from_phone = request.form.get("From", "").strip()
    body       = request.form.get("Body",  "").strip()

    reply_text = _handle_reply(from_phone, body)

    resp = MessagingResponse()
    resp.message(reply_text)
    return str(resp), 200, {"Content-Type": "text/xml"}


def _handle_reply(phone: str, text: str) -> str:
    entry = REPLY_MAP.get(text)
    if not entry:
        log.info("Unrecognized reply '%s' from %s", text, phone)
        return UNKNOWN_REPLY

    response, confirmation = entry

    db = Session()
    guest = db.query(Guest).filter_by(phone=phone).first()
    if not guest:
        db.close()
        log.warning("Reply from unknown number: %s", phone)
        return ""

    guest.response     = response
    guest.responded_at = datetime.datetime.utcnow()
    db.commit()
    name = guest.name
    db.close()
    log.info("Saved '%s' for %s (%s)", response, name, phone)
    return confirmation


# ── admin dashboard ────────────────────────────────────────────────────────────

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
