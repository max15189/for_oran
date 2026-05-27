import io
import os
import datetime
from functools import wraps

import openpyxl
from dotenv import load_dotenv
from flask import Flask, abort, render_template, request, send_file, Response

from models import Guest, Session

load_dotenv()

app = Flask(__name__)

ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123")
INVITATION_MESSAGE = os.getenv("INVITATION_MESSAGE", "You are invited!")
BASE_URL = os.getenv("BASE_URL", "http://localhost:5000")


def require_admin(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or auth.password != ADMIN_PASSWORD:
            return Response("Login required", 401, {"WWW-Authenticate": 'Basic realm="Admin"'})
        return f(*args, **kwargs)
    return decorated


@app.route("/rsvp")
def rsvp_page():
    token = request.args.get("token", "")
    change = request.args.get("change") == "1"
    db = Session()
    guest = db.query(Guest).filter_by(token=token).first()
    if not guest:
        db.close()
        abort(404)
    submitted = bool(guest.response) and not change
    result = render_template("rsvp.html", guest=guest, message=INVITATION_MESSAGE, submitted=submitted)
    db.close()
    return result


@app.route("/rsvp", methods=["POST"])
def rsvp_submit():
    token = request.form.get("token", "")
    response = request.form.get("response", "")
    if response not in ("yes", "no", "maybe"):
        abort(400)
    db = Session()
    guest = db.query(Guest).filter_by(token=token).first()
    if not guest:
        db.close()
        abort(404)
    guest.response = response
    guest.responded_at = datetime.datetime.utcnow()
    db.commit()
    result = render_template("rsvp.html", guest=guest, message=INVITATION_MESSAGE, submitted=True)
    db.close()
    return result


@app.route("/admin")
@require_admin
def admin():
    db = Session()
    guests = db.query(Guest).order_by(Guest.name).all()
    stats = {
        "total": len(guests),
        "yes": sum(1 for g in guests if g.response == "yes"),
        "no": sum(1 for g in guests if g.response == "no"),
        "maybe": sum(1 for g in guests if g.response == "maybe"),
        "pending": sum(1 for g in guests if not g.response),
    }
    base = BASE_URL.rstrip("/")
    result = render_template("admin.html", guests=guests, stats=stats, base_url=base)
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
            str(g.invited_at) if g.invited_at else "",
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
