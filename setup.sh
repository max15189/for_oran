#!/usr/bin/env bash
set -e

echo "Creating virtual environment..."
python3 -m venv .venv

echo "Activating virtual environment and installing dependencies..."
.venv/bin/pip install --upgrade pip -q
.venv/bin/pip install -r requirements.txt -q

if [ ! -f .env ]; then
    cp .env.example .env
    echo ""
    echo "Created .env from .env.example — please fill in your values before running."
else
    echo ".env already exists, skipping."
fi

echo ""
echo "Setup complete. Run the bot with:"
echo "  .venv/bin/python whatsapp_sender.py"
