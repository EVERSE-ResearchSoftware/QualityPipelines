PKGNAME=resqui

install:
	pip install .

install-dev:
	pip install -e .

venv:
	python3 -m venv venv

test:
	python3 run_tests.py

black:
	black src/$(PKGNAME)
	black doc/conf.py
	black tests
	black examples

clean:
	rm -rf venv

.PHONY: install install-dev venv test black clean
