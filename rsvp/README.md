# Wedding RSVP — SMS Bot (Twilio)

Guests receive an SMS with your invitation and reply **1**, **2**, or **3**.
They immediately get a confirmation back. Responses are saved to a database
you can view and export to Excel.

```
You  →  SMS:
         "test 123
          Please reply with:
          1 - Yes, I'll be there! ✓
          2 - Sadly I can't make it ✗
          3 - Not sure yet ?"

Guest  →  replies "1"

Server →  saves "yes" + auto-replies:
          "We're so happy you'll be joining us! See you there 🎉"
```

---

## What you need to sign up for

| Service | Why | Cost |
|---|---|---|
| **Twilio** (twilio.com) | Sends and receives the SMS messages | ~$10 total for 200 guests |
| **ngrok** (ngrok.com) | Gives your laptop a public URL so Twilio can reach it | Free |

---

## Step 1 — Sign up for Twilio

1. Go to **https://twilio.com** → click **"Sign up"**
2. Fill in your name, email, password — no credit card needed for the trial
3. Verify your email and phone number when prompted
4. You land on the **Console Dashboard** — keep this tab open

---

## Step 2 — Get a Twilio phone number

1. On the Console Dashboard click **"Get a phone number"** (or go to **Phone Numbers → Manage → Buy a number**)
2. Search for a number — any country works for sending to Israel
3. Click **"Buy"** — costs ~$1/month (covered by your free trial credit)
4. Note down the number (e.g. `+12025551234`)

---

## Step 3 — Collect your credentials

On the **Console Dashboard** (twilio.com/console) you will see:

| Variable | Where to find it |
|---|---|
| `TWILIO_ACCOUNT_SID` | Labeled **"Account SID"** on the dashboard |
| `TWILIO_AUTH_TOKEN` | Labeled **"Auth Token"** — click the eye icon to reveal |
| `TWILIO_FROM_NUMBER` | The phone number you just bought |

---

## Step 4 — Install ngrok

Ngrok gives your local server a public `https://` address so Twilio can
POST incoming SMS replies to it.

```bash
# Download from https://ngrok.com/download  OR on Linux/Mac:
snap install ngrok          # Linux
brew install ngrok          # Mac

# Authenticate (your token is on the ngrok dashboard after signing up):
ngrok config add-authtoken YOUR_NGROK_TOKEN
```

---

## Step 5 — Fill in your `.env`

```bash
cd rsvp
cp .env.example .env
```

Open `.env` and paste your values:

```
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=your_auth_token_here
TWILIO_FROM_NUMBER=+12025551234
ADMIN_PASSWORD=admin123
INVITATION_MESSAGE=test 123
```

---

## Step 6 — Run the setup and start the server

```bash
bash setup.sh                   # first time only — installs dependencies
.venv/bin/python app.py         # starts the server on port 5000
```

---

## Step 7 — Open an ngrok tunnel

In a **second terminal window**:

```bash
ngrok http 5000
```

You will see something like:
```
Forwarding   https://a1b2-34-56.ngrok-free.app -> http://localhost:5000
```

Copy that `https://` URL.

---

## Step 8 — Register the webhook in Twilio

This tells Twilio where to forward incoming SMS replies.

1. Go to **twilio.com/console → Phone Numbers → Manage → Active numbers**
2. Click your phone number
3. Scroll to **"Messaging Configuration"**
4. Under **"A message comes in"** set:
   - **Webhook**: `https://YOUR-NGROK-URL.ngrok-free.app/webhook`
   - Method: **HTTP POST**
5. Click **Save**

> Your Flask server must be running when Twilio forwards messages.

---

## Step 9 — Send the invitations

```bash
.venv/bin/python send_invitations.py
```

Each guest in `guests.csv` gets an SMS. The script skips anyone already
invited, so it's safe to run again if you add more guests.

---

## Step 10 — View responses

Open **http://localhost:5000/admin** in your browser.
- Username: anything
- Password: the `ADMIN_PASSWORD` from your `.env` (default: `admin123`)

Click **"Export to Excel"** to download all responses as a spreadsheet.

---

## Adding more guests

Edit `guests.csv`:
```
name,phone
Test Guest 1,0544359594
Test Guest 2,+972542663657
New Guest,0521234567
```

Then re-run `send_invitations.py` — it only sends to new guests.

---

## Cost estimate

| Item | Cost |
|---|---|
| Twilio phone number | ~$1/month |
| SMS to Israel (per message) | ~$0.05 |
| 200 guests (send + receive) | ~$15-20 total |
| Twilio free trial credit | $15 |
| **Out of pocket** | **~$5 after trial** |

---

## Important notes

- **ngrok free URL changes** every time you restart it. If you restart ngrok,
  go to Twilio → your number → update the webhook URL.
- For a permanent setup (no ngrok), deploy the Flask app to **Railway** or
  **Render** — both have free tiers and give you a fixed URL.
- The free Twilio trial lets you send to any number once you add credit.
  Upgrade from trial ($0, just add billing) to remove the "$15 trial" banner
  from outgoing messages.
