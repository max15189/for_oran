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
    echo "Created .env from .env.example — please fill in your WhatsApp credentials."
else
    echo ".env already exists, skipping."
fi

if [ ! -f config.yaml ]; then
    cp config.example.yaml config.yaml
    echo "Created config.yaml from config.example.yaml — please edit your search criteria."
else
    echo "config.yaml already exists, skipping."
fi

echo ""
echo "Setup complete."
echo "  1. Edit .env         (WhatsApp credentials)"
echo "  2. Edit config.yaml  (search criteria + Yad2 codes)"
echo "  3. Test:   .venv/bin/python run_once.py --dry-run"
echo "  4. Run:    .venv/bin/python main.py"
