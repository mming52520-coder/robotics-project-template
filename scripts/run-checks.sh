#!/usr/bin/env bash
set -euo pipefail

python tools/validate_template.py
python tools/validate_skills.py
python tools/validate_evals.py
python tools/validate_public_content.py
python -m unittest discover -s tests/unit -p 'test_*.py'
