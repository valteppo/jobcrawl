#!/usr/bin/env bash

if [ ! -d ".venv" ]; then
    python3 -m venv .venv
fi

# Check if root folder has permission to read and write and set recursively if not
if [ ! -r . ] || [ ! -w . ]; then
    sudo chmod -R u+rw .
fi

# Make src/main.py executable if not already
if [ ! -x src/main.py ]; then
    sudo chmod +x src/main.py
fi

if [ ! -d "applicant" ]; then
    mkdir applicant
    # Propmt user for cv.txt content
    echo    "Please enter your CV content. " \
            "Short description suffices 'Worked 3 years in the industry. Know C, Python, Rust. Experience with databases' etc. "\
            "Press Ctrl+D when done:\n"
    cat > applicant/cv.txt

    # Prompt user for ai instructions.txt content
    echo    "Please enter your AI instructions. " \
            "'Make tailored application for this company' or 'Do not apply to this job directly, explain why I am good choice for a trainee.' "\
            "Press Ctrl+D when done:\n"
    cat > applicant/ai_instructions.txt
fi

source .venv/bin/activate
pip install -r requirements.txt > /dev/null

# Wake up ollama server
ollama serve &
sleep 2

# Run the main Python script
python src/main.py

deactivate