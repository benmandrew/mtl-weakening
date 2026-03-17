.PHONY: all requirements tex

all: requirements tex

requirements:
	python3 requirements/count_requirements.py

tex:
	$(MAKE) -C paper/tex all
