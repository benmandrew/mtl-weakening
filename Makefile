.PHONY: all clean

MAIN = main
PDF = $(MAIN).pdf
BUILD_DIR = build

# LaTeX source files
TEX_FILES = $(MAIN).tex \
	paper/introduction.tex \
	paper/contexts.tex \
	paper/conclusion.tex \
	paper/appendix.tex \
	paper/algorithm/main.tex \
	paper/algorithm/cex-relative.tex \
	paper/algorithm/iterative.tex \
	paper/evaluation/main.tex \
	paper/evaluation/demonstration.tex \
	paper/evaluation/case-studies.tex

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
