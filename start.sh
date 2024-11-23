#!/bin/bash

# Check if venv directory exists
if [ ! -d "venv" ]; then
  # Create virtual environment called venv
  python3 -m venv venv
fi

# Activate the virtual environment
source venv/bin/activate

# Install required packages from requirements.txt
pip install -r "src/requirements.txt"

# Run the AI web researcher script
python -m src

deactivate