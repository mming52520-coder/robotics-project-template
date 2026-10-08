# Read-only review record

Create the machine-readable record with `python3 tools/review_coverage.py create`.
It is written under ignored `artifacts/`; fill its `reviewed_paths`, `findings`, and
`evidence_runs` after inspection. Do not edit its base, head, snapshot, contract digest,
or changed-file inventory. Run `python3 tools/review_coverage.py validate <record.json>`.
For each finding, use a stable local ID and include `path`, positive `line`,
`contract`, `trigger`, and `status` (`OPEN`, `PENDING`, `FIXED`, `FALSE_POSITIVE`,
`DUPLICATE`, or `OUT_OF_SCOPE`). Closed findings need `resolution`; `FIXED` also needs
`verification`. Any skipped path or open finding keeps validation blocked.

Use prose only for context that the JSON cannot prove:

- Reviewer mode: self-review / separate reviewer / OCR
- Candidate and tested SHAs:
- Tested workspace snapshot digest and review time:
- ChangeContract path and digest:
- Files expected / reviewed / excluded and reasons:
- Offline and ROS manifests:
- JUnit cases and skipped or missing cases:
- Confirmed findings with file, line, violated contract, and regression:
- False positives, duplicates, out-of-scope, or pending findings:
- Fixes and fresh evidence after each confirmed finding:
- Human decision required; JSON never proves an independent human review:
