.PHONY: run test fmt lint ruff pylint

run:
	python3 -m src.main

test:
	PYTHONPATH=src python3 -m unittest discover -s tests -p "test_*.py"

fmt:
	python3 -m black -l 80 .

lint: ruff pylint mypy

ruff:
	python3 -m ruff check

pylint:
	find . -name "*.py" -not -path "*/.*" | PYTHONPATH=src xargs python3 -m pylint --errors-only

mypy:
	find . -name "*.py" -not -path "*/.*" | PYTHONPATH=src xargs python3 -m mypy --check-untyped-defs --ignore-missing-imports
