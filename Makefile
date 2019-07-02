.PHONY: clean clean-test clean-pyc clean-build help venv
.DEFAULT_GOAL := help


define PRINT_HELP_PYSCRIPT
import re, sys

for line in sys.stdin:
	match = re.match(r'^([a-zA-Z_-]+):.*?## (.*)$$', line)
	if match:
		target, help = match.groups()
		print("%-20s %s" % (target, help))
endef
export PRINT_HELP_PYSCRIPT

all: clean build test dist

help:
	@python -c "$$PRINT_HELP_PYSCRIPT" < $(MAKEFILE_LIST)

jenkins: clean test dist

clean: clean-build clean-pyc clean-test ## remove all build, test, coverage and Python artifacts

clean-build: ## remove build artifacts
	rm -fr build/
	rm -fr dist/
	rm -fr .eggs/
	find . -name '*.egg-info' -not -path './venv-make/*' -not -path './venv/*' -exec rm -fr {} +
	find . -name '*.egg' -not -path './venv-make/*' -not -path './venv/*' -exec rm -f {} +

clean-pyc: ## remove Python file artifacts
	find . -name '*.pyc' -exec rm -f {} +
	find . -name '*.pyo' -exec rm -f {} +
	find . -name '*~' -exec rm -f {} +
	find . -name '__pycache__' -exec rm -fr {} +

clean-test: ## remove test and coverage artifacts
	rm -fr .tox/
	rm -f .coverage
	rm -fr htmlcov/
	rm -fr .pytest_cache
	rm -f nose2-junit.xml

test: venv ## run tests quickly with the default Python
	venv_make/bin/python setup.py test

dist:  venv  clean ## builds source and wheel package
	venv_make/bin/python setup.py sdist
	venv_make/bin/python setup.py bdist_wheel
	ls -l dist

install: clean venv  ## install the package to the active Python's site-packages
	python setup.py install

venv: setup.py
	which virtualenv
	virtualenv venv_make --python=python3
	venv_make/bin/pip install --upgrade pip setuptools wheel
	venv_make/bin/python --version