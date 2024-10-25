rm -rf build
rm -rf dist
python -m venv build-venv
source build-venv/bin/activate
pip install -U setuptools
python setup.py sdist bdist_wheel
rm -rf build-venv
