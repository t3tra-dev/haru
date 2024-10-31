rm -rf build
rm -rf dist
python -m venv .build-venv
source .build-venv/bin/activate
pip install -U setuptools
python setup.py sdist bdist_wheel
rm -rf .build-venv

python3 -m venv .test-venv
source .test-venv/bin/activate
pip install -e .
clear
cd tests
python frontend.py
rm -rf .test-venv
