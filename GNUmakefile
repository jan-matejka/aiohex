.DEFAULT_GOAL := build

DOCDIR = ./Documentation
DOCMAKE = $(MAKE) -C $(DOCDIR)

build:

.PHONY: doc
doc:

	$(DOCMAKE) html

.PHONY: clean
clean:

	$(DOCMAKE) clean

.PHONY: check
check:

	python $(shell which py.test) -v
