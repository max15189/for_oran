# WhatsApp Hourly Question Bot

Sends a random question to a WhatsApp number once every hour using the WhatsApp Cloud API.

---

## Setup

### Step 1 — Create a Meta Developer account

1. Go to **https://developers.facebook.com**
2. Log in with your Facebook account
3. Click **"Get Started"** if it's your first time

---

### Step 2 — Create an App

1. Click **"My Apps"** → **"Create App"**
2. Choose **"Business"** as the app type
3. Give it any name (e.g. `my-whatsapp-bot`)
4. Click **Create**

---

### Step 3 — Add WhatsApp to your app

1. In your app dashboard, scroll down to find **WhatsApp**
2. Click **"Set up"**
3. Meta provides a free test phone number to send from — no purchase needed

---

### Step 4 — Collect your credentials

On the **WhatsApp → Getting Started** page you will find everything you need:

| Variable | Where to find it |
|---|---|
| `WHATSAPP_API_URL` | Shown as the full API URL with your Phone Number ID already filled in. Looks like: `https://graph.facebook.com/v19.0/YOUR_PHONE_NUMBER_ID/messages` |
| `WHATSAPP_TOKEN` | Listed as **"Temporary access token"** (valid 24 h for testing). For permanent use, generate one via **System Users** in Meta Business Settings |
| `RECIPIENT_PHONE` | Your phone number in international format, **no leading +**. Example for Israel: `972501234567` |

---

### Step 5 — Add yourself as a test recipient

1. On the same "Getting Started" page, find the **"To"** field
2. Enter your phone number and click **"Send Message"** once to verify it
3. After that the bot can message that number freely

---

## Running the bot

```bash
# 1. Run the one-time setup (creates virtual env and installs dependencies)
bash setup.sh

# 2. Fill in your credentials
nano .env

# 3. Start the bot
.venv/bin/python whatsapp_sender.py
```

The bot sends one question immediately on startup, then one every hour.
Logs are written to both the terminal and `whatsapp_sender.log`.

---

## Project structure

```
.
├── whatsapp_sender.py   # Main bot logic
├── questions.py         # Pool of random questions
├── requirements.txt     # Python dependencies
├── setup.sh             # One-shot environment setup
├── .env.example         # Credentials template
└── .env                 # Your actual credentials (never committed)
```

---

## .env file

Copy `.env.example` to `.env` and fill in your values:

```
WHATSAPP_API_URL=https://graph.facebook.com/v19.0/YOUR_PHONE_NUMBER_ID/messages
WHATSAPP_TOKEN=YOUR_ACCESS_TOKEN_HERE
RECIPIENT_PHONE=972501234567
```
