#!/usr/bin/env bash
set -euo pipefail

if [[ -d tests ]]; then
  echo "Replace this placeholder with project-specific unit, integration, and replay checks."
else
  echo "tests directory is missing" >&2
  exit 1
fi
