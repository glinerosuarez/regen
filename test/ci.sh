#!/bin/bash

set -e

# Linter
pip install flake8
flake8 . --max-line-length=120 --exclude=test,__init__.py

# Tests
pip install pytest
pytest -vv .
