PKGNAME=resqui

install:
	pip install .

install-dev:
	pip install -e ".[dev]"

venv:
	python3 -m venv venv

test:
	python3 run_tests.py

example:
	resqui -c example.json https://github.com/JuliaHEP/UnROOT.jl

black:
	black src/$(PKGNAME)
	black tests

clean:
	rm -rf venv

.PHONY: install install-dev venv test example black clean
