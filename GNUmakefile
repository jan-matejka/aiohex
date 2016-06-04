.DEFAULT_GOAL := build

PKGNAME = aiohex

DOCDIR = ./Documentation
DOCMAKE = $(MAKE) -C $(DOCDIR)

TESTDIR = ./tests

build:

.PHONY: doc
doc:

	$(DOCMAKE) html

.PHONY: clean
clean:

	$(DOCMAKE) clean

.PHONY: check
check:

	python $(shell which py.test) -v --doctest-modules $(PKGNAME) $(TESTDIR)
