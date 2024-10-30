#!/usr/bin/env bash

set -e
set -x

mypy poetry_plugin_version
ruff format poetry_plugin_version tests --check
ruff check poetry_plugin_version tests
