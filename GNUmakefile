.DEFAULT_GOAL := build

PKGNAME = aiohex

DOCDIR = ./Documentation
DOCMAKE = $(MAKE) -C $(DOCDIR)

TESTDIR = ./tests
CRAMTESTS = $(shell find $(TESTDIR)/cram/ -type f -name '*.t')

build:

.PHONY: doc
doc:

	$(DOCMAKE) html

.PHONY: clean
clean:

	$(DOCMAKE) clean

.PHONY: check
check: pytest cram

.PHONY: pytest
pytest:

	python $(shell which py.test) -v --doctest-modules $(PKGNAME) $(TESTDIR)

.PHONY: cram
cram:

	cram --shell=/bin/zsh $(CRAMTESTS)
