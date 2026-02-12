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

vulture:
	find . -name "*.py" -not -path "*/.*" | PYTHONPATH=src xargs python3 -m vulture

bandit:
	python3 -m bandit -c pyproject.toml --exclude "./.venv" -r . -q


.PHONY: all clean

MAIN = main
PDF = $(MAIN).pdf
BUILD_DIR = build

# LaTeX source files
TEX_FILES = $(wildcard *.tex paper/*.tex paper/*/*.tex)

# Bibliography and style files
BIB_FILES = bibliography.bib
BST_FILES = splncs04.bst
CLS_FILES = llncs.cls

PDFLATEX_FLAGS = -output-directory=$(BUILD_DIR) -interaction=nonstopmode -halt-on-error

all: $(PDF)

$(PDF): $(TEX_FILES) $(BIB_FILES) $(BST_FILES) $(CLS_FILES)
	mkdir -p $(BUILD_DIR)
	pdflatex $(PDFLATEX_FLAGS) $(MAIN)
	biber --output-directory $(BUILD_DIR) $(MAIN)
	pdflatex $(PDFLATEX_FLAGS) $(MAIN)
	pdflatex $(PDFLATEX_FLAGS) $(MAIN)
	cp $(BUILD_DIR)/$(PDF) .

clean:
	rm -rf $(BUILD_DIR)
	rm -f paper/*.aux paper/*/*.aux

cleanall: clean
	rm -f $(PDF)
