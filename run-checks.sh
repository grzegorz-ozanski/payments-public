#!/usr/bin/env bash

pytest --cov=payments --cov=providers --cov=lookuplist --cov-report=term --cov-report=html
mypy . --strict --ignore-missing-imports --exclude run
ruff check .
rm -rf error
