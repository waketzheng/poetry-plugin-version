#!/usr/bin/env bash

set -e
set -x

coverage run --source=poetry_plugin_version,tests -m pytest "${@}"
coverage combine
coverage xml
