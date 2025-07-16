.PHONY: run test fmt lint ruff pylint

run:
	python3 src/main.py

test:
	python3 -m unittest

fmt:
	python3 -m black -l 80 .

lint: ruff pylint mypy

ruff:
	python3 -m ruff check

pylint:
	find . -name "*.py" -not -path "*/.*" | xargs python3 -m pylint --errors-only

mypy:
	find . -name "*.py" -not -path "*/.*" | xargs python3 -m mypy --check-untyped-defs
