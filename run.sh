#!/usr/bin/env bash

if [ ! -d ".venv" ]; then
    python3 -m venv .venv
fi

if [ ! -d "applicant" ]; then
    mkdir applicant
fi

source .venv/bin/activate
pip install -r requirements.txt > /dev/null

python src/main.py

deactivate