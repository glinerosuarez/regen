#!/bin/bash

set -e

# Formatter
pip install black
black -l 120 -t py37 --check .

# Linter
pip install flake8
flake8 . --max-line-length=120 --exclude=test,__init__.py --ignore=E203,W504,W503

# Tests
pip install pytest
pytest -vv --full-trace
