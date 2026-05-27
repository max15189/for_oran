#!/usr/bin/env bash
set -e
cd "$(dirname "$0")"

echo "Creating virtual environment..."
python3 -m venv .venv

echo "Installing dependencies..."
.venv/bin/pip install --upgrade pip -q
.venv/bin/pip install -r requirements.txt -q

echo "Generating test invitation image..."
.venv/bin/python create_test_image.py

if [ ! -f .env ]; then
    cp .env.example .env
    echo ""
    echo "Created .env — fill in WHATSAPP_API_URL and WHATSAPP_TOKEN before running."
fi

echo ""
echo "Setup complete."
echo ""
echo "  Start the server:   .venv/bin/python app.py"
echo "  Send invitations:   .venv/bin/python send_invitations.py"
echo "  Admin dashboard:    http://localhost:5000/admin  (password: admin123)"
