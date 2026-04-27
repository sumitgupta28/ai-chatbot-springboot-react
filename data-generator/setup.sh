#!/bin/bash

set -e

VENV_DIR=".venv"
SCRIPT="generate_bills.py"

echo "Creating virtual environment..."
python3 -m venv "$VENV_DIR"

echo "Activating virtual environment..."
source "$VENV_DIR/bin/activate"

echo "Installing requirements..."
pip install -r requirements.txt

echo "Running script..."
python "$SCRIPT"

deactivate
echo "Done."
