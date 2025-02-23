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

up:
	poetry update --verbose

deps:
ifeq ($(wildcard poetry.lock),)
	poetry lock --verbose
	poetry install --verbose
else
	poetry install
endif

_check:
	poetry run ./scripts/lint.sh
check: deps _build _check

_lint:
	poetry run fast lint
lint: deps _build _lint

_test:
	poetry run ./scripts/test.sh
test: deps _test

_style:
	poetry run ./scripts/format.sh
style: deps _style

_build:
	rm -fR dist/
	poetry build
build: deps _build

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
