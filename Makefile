.PHONY: test unittest expect_test fmt fmt-ci lint ruff pylint mypy bandit

all: fmt lint test

test: unittest expect_test

unittest:
	PYTHONPATH=src python3 -m unittest discover -s tests -p "test_*.py"

EXPECT_TESTS := $(wildcard tests/test_*.exp)

expect_test:
	@for t in $(EXPECT_TESTS); do \
		echo "Running $$t..."; \
		expect -- $$t || { echo "Test $$t FAILED"; exit 1; }; \
	done
	@echo "All expect tests passed!"

fmt:
	python3 -m black -l 80 .

fmt-ci:
	python3 -m black --check -l 80 .

lint: ruff-fix pylint mypy bandit

ruff:
	python3 -m ruff check

ruff-fix:
	python3 -m ruff check --fix

pylint:
	find . -name "*.py" -not -path "*/.*" | PYTHONPATH=src xargs python3 -m pylint --score=n

mypy:
	find . -name "*.py" -not -path "*/.*" | PYTHONPATH=src xargs python3 -m mypy --strict

bandit:
	python3 -m bandit -c pyproject.toml --exclude "./.venv" -r . -q
