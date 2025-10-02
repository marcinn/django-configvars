.PHONY: dev-setup docs-setup docs docs-clean docs-serve fmt lint syntaxcheck check test test-pytest test-tox package upload clean

VENV := .env
VENV_PYTHON := $(VENV)/bin/python
VENV_PIP := $(VENV_PYTHON) -m pip --isolated
PIP_CLEAN_ENV := PIP_CONFIG_FILE=/dev/null PIP_USER=0
PY_FILES := configvars tests example
DOCS_PORT ?= 8765

$(VENV)/bin/python:
	python -m venv $(VENV)

$(VENV)/.dev-installed: pyproject.toml | $(VENV)/bin/python
	$(VENV_PIP) install -e ".[dev]"
	touch $(VENV)/.dev-installed

$(VENV)/.docs-installed: docs/requirements.txt | $(VENV)/.dev-installed
	$(VENV_PIP) install -r docs/requirements.txt
	touch $(VENV)/.docs-installed

dev-setup: $(VENV)/.dev-installed

docs-setup: $(VENV)/.docs-installed

docs: $(VENV)/.docs-installed
	$(VENV)/bin/python -m sphinx -b html docs docs/_build/html

docs-clean:
	rm -rf docs/_build

docs-serve: docs
	$(VENV)/bin/python -m http.server --directory docs/_build/html $(DOCS_PORT)

fmt: $(VENV)/.dev-installed
	$(VENV)/bin/isort $(PY_FILES)
	$(VENV)/bin/black $(PY_FILES)

lint: $(VENV)/.dev-installed
	$(VENV)/bin/isort --check-only $(PY_FILES)
	$(VENV)/bin/black --check $(PY_FILES)

syntaxcheck: $(VENV)/.dev-installed
	$(VENV_PYTHON) -m compileall -q $(PY_FILES)

test-pytest: $(VENV)/.dev-installed
	PYTHONPATH=. $(VENV)/bin/pytest -q || [ $$? -eq 5 ]

test-tox:
	tox

test: test-pytest

check: syntaxcheck lint test-pytest

coverage: $(VENV)/.dev-installed
	PYTHONPATH=. $(VENV)/bin/coverage run -m pytest tests -q || [ $$? -eq 5 ]
	$(VENV)/bin/coverage report -m

package: $(VENV)/.dev-installed
	$(PIP_CLEAN_ENV) $(VENV_PYTHON) -m build

upload: package
	$(VENV)/bin/twine upload dist/*

clean:
	rm -rf $(VENV) dist
