PKGNAME=resqui
VENV=venv
PYTHON=$(VENV)/bin/python
PIP=$(VENV)/bin/pip

$(VENV)/bin/activate:
	python3 -m venv $(VENV)
	$(PIP) install -e ".[dev,docs]"

install: $(VENV)/bin/activate

install-dev: $(VENV)/bin/activate

install-docs: $(VENV)/bin/activate

venv: $(VENV)/bin/activate

test: $(VENV)/bin/activate
	$(PYTHON) run_tests.py

example: $(VENV)/bin/activate
	$(VENV)/bin/resqui -c configurations/basic.json

black: $(VENV)/bin/activate
	$(VENV)/bin/black src/$(PKGNAME)
	$(VENV)/bin/black tests

docs: $(VENV)/bin/activate
	$(VENV)/bin/mkdocs build

docs-serve: $(VENV)/bin/activate
	$(VENV)/bin/mkdocs serve

clean:
	rm -rf venv site

.PHONY: install install-dev install-docs venv test example black docs docs-serve clean
