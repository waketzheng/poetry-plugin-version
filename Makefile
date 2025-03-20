help:
	@echo  "poetry-plugin-version development makefile"
	@echo
	@echo  "Usage: make <target>"
	@echo  "Targets:"
	@echo  "    up      Updates dev/test dependencies"
	@echo  "    deps    Ensure dev/test dependencies are installed"
	@echo  "    check   Checks that build is sane"
	@echo  "    test    Runs all tests"
	@echo  "    style   Auto-formats the code"
	@echo  "    lint    Auto-formats the code and check type hints"
	@echo  "    venv    Create virtual environment"

up:
	poetry update --verbose

deps:
ifeq ($(wildcard poetry.lock),)
	poetry lock --verbose
	poetry install --all-extras --all-groups --verbose
else
	poetry install --all-extras --all-groups
endif
ifeq ($(shell poetry run --no-plugins which ruff),)
	@echo 'Command "ruff" not found! You may need to install it by `pipx install ruff`'
endif

_check:
	poetry run ./scripts/lint.sh
check: deps build _check

_lint:
	poetry run fast lint
lint: deps build _lint

test:
ifeq ($(shell poetry run --no-plugins which coverage),)
	poetry install --with=test
endif
	poetry run ./scripts/test.sh

_style:
	poetry run ./scripts/format.sh

style:
ifeq ($(shell poetry run --no-plugins which ruff),)
	@echo 'Command "ruff" not found! You may need to install it by `pipx install ruff`'
endif
	$(MAKE) _style

build:
	poetry build --clean

# Usage::
#   make venv version=3.12
venv:
	poetry env use python$(version)
	$(MAKE) deps
	poetry run pip install --upgrade pip

venv39:
	poetry venv use python3.9
	$(MAKE) deps

venv313:
	$(MAKE) venv version=3.13
