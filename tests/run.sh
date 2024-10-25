python3 -m venv .test-venv
source .test-venv/bin/activate
pip install -e .[all]
clear
cd tests
python main.py
