.PHONY: apidoc html clean

SPHINXBUILD := sphinx-build
SOURCEDIR := src
BUILDDIR := build
APIDOCDIR := $(SOURCEDIR)/_api
SOURCEPKG := ../src

apidoc:
	sphinx-apidoc -f -e -o $(APIDOCDIR) $(SOURCEPKG)
	for f in $(APIDOCDIR)/*.rst; do \
		sed -i '1s/^src\.//' "$$f"; \
	done

html: apidoc
	$(SPHINXBUILD) -W -b html $(SOURCEDIR) $(BUILDDIR)/html

clean:
	rm -rf $(BUILDDIR)
