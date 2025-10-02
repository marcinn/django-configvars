.PHONY: dev-setup docs-setup docs docs-html docs-multiversion docs-clean docs-serve fmt lint syntaxcheck check test test-pytest test-tox package upload clean

VENV := .env
VENV_PYTHON := $(VENV)/bin/python
VENV_PIP := $(VENV_PYTHON) -m pip --isolated
PIP_CLEAN_ENV := PIP_CONFIG_FILE=/dev/null PIP_USER=0
PY_FILES := configvars tests example
DOCS_PORT ?= 8765
DOCS_HTML_DIR := docs/_build/html
DOCS_MULTIVERSION_DIR := docs/_build/multiversion

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
	@LATEST_TAG="$$(git for-each-ref --sort=-version:refname --format='%(refname:strip=2)' refs/tags | grep -E '^(v)?[0-9]+\.[0-9]+\.[0-9]+$$' | head -n1 || true)"; \
	if [ -n "$$LATEST_TAG" ]; then \
		DOCS_LATEST_VERSION="$$LATEST_TAG" $(VENV)/bin/sphinx-multiversion docs $(DOCS_MULTIVERSION_DIR); \
	else \
		$(VENV)/bin/sphinx-multiversion docs $(DOCS_MULTIVERSION_DIR); \
	fi
	@DOCS_DIR="$(DOCS_MULTIVERSION_DIR)"; \
	latest_tag="$$(git for-each-ref --sort=-version:refname --format='%(refname:strip=2)' refs/tags | grep -E '^(v)?[0-9]+\.[0-9]+\.[0-9]+$$' | head -n1 || true)"; \
	if [ -n "$$latest_tag" ] && [ -f "$$DOCS_DIR/$$latest_tag/index.html" ]; then \
		latest_src="$$latest_tag"; \
	else \
		first_dir="$$(ls -1d "$$DOCS_DIR"/*/ 2>/dev/null | head -n1 || true)"; \
		if [ -z "$$first_dir" ]; then \
			echo "No built documentation versions found in $$DOCS_DIR" >&2; \
			exit 1; \
		fi; \
		latest_src="$$(basename "$${first_dir%/}")"; \
	fi; \
	rm -f "$$DOCS_DIR/index.html"; \
	rm -rf "$$DOCS_DIR/latest"; \
	cp -a "$$DOCS_DIR/$$latest_src" "$$DOCS_DIR/latest"; \
	printf '%s\n' \
		'<!doctype html>' \
		'<html lang="en">' \
		'<head>' \
		'  <meta charset="utf-8">' \
		'  <meta http-equiv="refresh" content="0; url=./latest/">' \
		'  <meta name="viewport" content="width=device-width, initial-scale=1">' \
		'  <title>Redirecting...</title>' \
		'</head>' \
		'<body>' \
		'  <p>Redirecting to <a href="./latest/">latest/</a></p>' \
		'</body>' \
		'</html>' \
		> "$$DOCS_DIR/index.html"; \
	touch "$$DOCS_DIR/.nojekyll"

docs-html: $(VENV)/.docs-installed
	$(VENV)/bin/python -m sphinx -b html docs $(DOCS_HTML_DIR)

docs-multiversion: $(VENV)/.docs-installed
	$(MAKE) docs

docs-clean:
	rm -rf docs/_build

docs-serve: docs
	@echo "Serving $(DOCS_MULTIVERSION_DIR) on http://127.0.0.1:$(DOCS_PORT) (open /latest/)"
	$(VENV)/bin/python -m http.server --directory $(DOCS_MULTIVERSION_DIR) $(DOCS_PORT)

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
