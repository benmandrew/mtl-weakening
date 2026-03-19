.PHONY: apidoc html clean

SPHINXBUILD := sphinx-build
SOURCEDIR := src
BUILDDIR := build
APIDOCDIR := $(SOURCEDIR)/_api
SOURCEPKG := ../src

apidoc:
	sphinx-apidoc -f -e -o $(APIDOCDIR) $(SOURCEPKG)
	for f in $(APIDOCDIR)/*.rst; do \
		sed '1s/^src\.//' "$$f" > "$$f.tmp" && mv "$$f.tmp" "$$f"; \
	done
	rm -f $(APIDOCDIR)/modules.rst $(APIDOCDIR)/src.rst

html: apidoc
	$(SPHINXBUILD) -W -b html $(SOURCEDIR) $(BUILDDIR)/html

clean:
	rm -rf $(BUILDDIR)
