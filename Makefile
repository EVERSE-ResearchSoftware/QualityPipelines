PKGNAME=resqui
VENV=venv
PYTHON=$(VENV)/bin/python
PIP=$(VENV)/bin/pip
COVERAGE=$(VENV)/bin/coverage

$(VENV)/bin/activate: pyproject.toml
	python3 -m venv $(VENV)
	$(PIP) install -e ".[dev,docs]"
	touch $(VENV)/bin/activate

install: $(VENV)/bin/activate

install-dev: $(VENV)/bin/activate

install-docs: $(VENV)/bin/activate

venv: $(VENV)/bin/activate

test: $(VENV)/bin/activate
	$(COVERAGE) run -m unittest discover -s tests
	$(COVERAGE) report -m

coverage: $(VENV)/bin/activate
	$(COVERAGE) run -m unittest discover -s tests
	$(COVERAGE) html
	$(COVERAGE) report -m

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
	rm -rf venv site htmlcov .coverage

.PHONY: install install-dev install-docs venv test coverage example black docs docs-serve clean
