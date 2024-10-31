rm -rf build
rm -rf dist
python -m venv .build-venv
source .build-venv/bin/activate
pip install -U setuptools
python setup.py sdist bdist_wheel
rm -rf .build-venv

python3 -m venv .test-venv
source .test-venv/bin/activate
pip install -U uvicorn
pip install -e .
clear
cd tests
uvicorn asgi:asgi_app --reload
rm -rf .test-venv
