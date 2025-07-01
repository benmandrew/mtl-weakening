.PHONY: fmt lint ruff pylint

fmt:
	python3 -m black -l 80 .

lint: ruff pylint

ruff:
	python3 -m ruff check

pylint:
	find . -name "*.py" -not -path "*/.*" | xargs python3 -m pylint --errors-only
