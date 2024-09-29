#!/bin/bash
PROJECT=restsh

set -e
set -o pipefail
source .venv/bin/activate
python -m compileall -l .
mypy -p $PROJECT
pylint $PROJECT/*.py #$PROJECT/*/*.py
#pytest --disable-warnings tests/
python setup.py check && echo " ...passed."
