#!/bin/bash

set -e

# Formatter
pip install black
black -l 120 -t py310 --check .

# Linter
pip install flake8
flake8 . --max-line-length=120 --exclude=test,__init__.py --ignore=E203

# Tests
pip install pytest
pytest -vv .
