# Wedding RSVP — WhatsApp Bot

Guests receive a WhatsApp message with your invitation and reply **1**, **2**, or **3**.
Responses are saved to a database. You view them at `/admin` and export to Excel.

```
You  →  WhatsApp message:
         "test 123
          Reply with:
          1 - Yes, I'll be there! ✓
          2 - Sadly I can't make it ✗
          3 - Not sure yet ?
          Just send 1, 2, or 3"

Guest  →  replies "1" in WhatsApp

Meta   →  POST /webhook  (your server)

Server →  saves "yes" to database
```

---

## What you need to sign up for

| Service | Why | Cost |
|---|---|---|
| **Meta Developer** (developers.facebook.com) | To send WhatsApp messages and receive replies | Free |
| **ngrok** (ngrok.com) | To give your local server a public URL so Meta can reach it | Free tier is enough |

---

## Step 1 — Meta Developer account

1. Go to **https://developers.facebook.com**
2. Log in with your Facebook account
3. Click **"Get Started"** and follow the verification steps if it's your first time

---

## Step 2 — Create a Meta App

1. Click **"My Apps"** (top right) → **"Create App"**
2. Choose **"Other"** → **"Business"**
3. Give it any name (e.g. `wedding-rsvp`) → click **Create App**

---

## Step 3 — Add WhatsApp to the app

1. In your app dashboard, scroll down and find **WhatsApp** → click **"Set up"**
2. You land on the **"Getting Started"** page — keep this tab open

---

## Step 4 — Collect your credentials

On the **WhatsApp → Getting Started** page:

**`WHATSAPP_API_URL`**
Look for the sample curl command. Copy the URL — it looks like:
```
https://graph.facebook.com/v19.0/123456789012345/messages
```

**`WHATSAPP_TOKEN`**
Labeled **"Temporary access token"** — copy it.
> It expires after 24 hours. For permanent use: go to
> **Meta Business Settings → System Users → Add → Generate Token** and select your app.

**Add test recipients**
- On the same page, find the **"To"** phone number field
- Enter each guest number and click **"Send Message"** to verify them
- The two numbers in `guests.csv` must be added here before running

---

## Step 5 — Set up ngrok

Ngrok gives your local server a public `https://` URL so Meta can send webhook events to it.

### Install
```bash
# Download from https://ngrok.com/download  OR on Linux:
snap install ngrok
# Then authenticate (token is on your ngrok dashboard):
ngrok config add-authtoken YOUR_NGROK_TOKEN
```

### Start a tunnel
Open a **separate terminal** and run:
```bash
ngrok http 5000
```

You will see something like:
```
Forwarding   https://a1b2-34-56.ngrok-free.app -> http://localhost:5000
```

Copy that `https://` URL — you need it in the next step.

---

## Step 6 — Fill in your `.env`

```bash
cp .env.example .env
```

Edit `.env` and fill in:

```
WHATSAPP_API_URL=https://graph.facebook.com/v19.0/YOUR_PHONE_NUMBER_ID/messages
WHATSAPP_TOKEN=your_token_here
WEBHOOK_VERIFY_TOKEN=my_secret_token_123   ← pick any string, you'll reuse it below
ADMIN_PASSWORD=admin123
INVITATION_MESSAGE=test 123
```

---

## Step 7 — Run the server

```bash
bash setup.sh          # first time only: installs dependencies
.venv/bin/python app.py
```

The server starts on **http://localhost:5000**

---

## Step 8 — Register the webhook in Meta

This tells Meta where to send guest replies.

1. In the Meta developer console go to **WhatsApp → Configuration** (left sidebar)
2. Under **Webhook** click **"Edit"**
3. Fill in:
   - **Callback URL**: `https://YOUR-NGROK-URL.ngrok-free.app/webhook`
   - **Verify token**: the same string you put in `WEBHOOK_VERIFY_TOKEN` in `.env`
4. Click **"Verify and Save"** — Meta will call your server to confirm it's running
5. After saving, click **"Subscribe"** next to the **messages** field

> Your Flask server must be running when you click "Verify and Save".

---

## Step 9 — Send invitations

```bash
.venv/bin/python send_invitations.py
```

Each guest in `guests.csv` gets a WhatsApp message with the invitation and reply instructions.

---

## Step 10 — View responses

Open **http://localhost:5000/admin** in your browser.
- Username: anything
- Password: whatever you set in `ADMIN_PASSWORD` (default: `admin123`)

Click **"Export to Excel"** to download all responses.

---

## Adding more guests

Edit `guests.csv` — add a row per guest:
```
name,phone
Test Guest 1,0544359594
Test Guest 2,+972542663657
New Guest,0521234567
```

Then re-run `send_invitations.py`. It skips guests already in the database.

---

## Important notes

- **ngrok free URL changes** every time you restart ngrok. If you restart, go back to Meta → WhatsApp → Configuration and update the webhook URL.
- For a permanent public URL (no ngrok), deploy the Flask app to **Railway**, **Render**, or any VPS — all have free tiers.
- Guests must have been added as test recipients in Meta (Step 4) to receive messages during testing.
