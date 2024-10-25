python3 -m venv .test-venv
source .test-venv/bin/activate
pip install -e .
clear
python tests/main.py
