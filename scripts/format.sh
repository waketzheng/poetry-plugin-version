#!/usr/bin/env bash

set -e
set -x

ruff format poetry_plugin_version tests
ruff check --fix poetry_plugin_version tests
