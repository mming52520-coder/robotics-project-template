# AI delivery chain candidate acceptance

- Date: 2026-10-08
- Candidate branch: `codex/ai-delivery-chain` in an independent worktree
- Base: local PR #18 acceptance commit `c41341f8d586fe03ab5b355a921ec84aafbca79f`
- Remote PR #18 head at baseline: `1b23621`; remote `main`: `94bd793`
- Candidate state: local branch; no push, merge, or GitHub setting mutation

## Gate results

| Gate | Result | Evidence and limit |
| --- | --- | --- |
| PR #18 baseline and design safety | PASS | Prior report `pr18-engineering-acceptance.md`; no ROS control code changed on this branch. |
| DesignPackage v2 and legacy boundary | PASS | Three v2 examples validated; explicit v1 design-only mode rejects evidence claims. |
| ChangeContract scope | PASS | `changes/ai-delivery-chain/change.json`; allowed paths and executable test IDs checked against actual diff. |
| Requirement to ROS and test links | PASS | Existing v2 trace validated against four passing Jazzy JUnit cases. |
| Offline repository gates | PASS | Shared runner: 51 unit tests, template, Skills, eval fixtures, public scan, three design examples, contract, Ruff, YAML, Markdown, ShellCheck. |
| Local Jazzy simulation gates | PASS | One package builds; four ROS tests pass; JUnit trace and `colcon test-result` pass. Simulation only. |
| Missing/skipped test and out-of-scope negatives | PASS | Unit cases reject skipped or missing JUnit links, fake approval, and out-of-scope paths. |
| OCR model review and file preview | BLOCKED | OCR CLI was not installed locally; rule matching and model output cannot be claimed. |
| Agent behavior evaluations | NOT RUN | Three workflow case definitions exist; no Agent run or tool-operation trace exists. |
| Fresh GitHub CI on this branch | NOT RUN | Branch has not been pushed; uploaded CI artifacts do not exist. |
| GitHub required PR/check rules | BLOCKED | Existing ruleset lacks required PR and status checks; changing remote settings awaits candidate CI and owner decision. |
| Human acceptance and merge | BLOCKED | A maintainer must inspect policy/test changes and final CI evidence; no merge authorization. |

## Reproduction and raw evidence

From the repository root, install `requirements-dev.txt` in a development environment,
then run:

```bash
bash scripts/run-checks.sh
bash scripts/run-ros-checks.sh
python3 tools/evidence.py validate artifacts/<offline-run-id>
python3 tools/evidence.py validate artifacts/<ros-run-id>
git diff --check
```

The runners print every executed command and write its combined raw output to
`artifacts/<run-id>/<number>-<check>.log`. Each `manifest.json` binds the command,
exit status, log hash, policy and test hashes, DesignPackage digest, base and candidate
SHAs, tested checkout SHA, and local dirty/untracked inputs. The ROS manifest also
binds the JUnit file and each implemented test ID to a case result. A report copied
without its raw logs or reused after changing repository inputs fails validation.

## Changed file groups and review focus

- `contracts/`, `tools/design_contracts.py`, `tools/validate_design_package.py`:
  versioned structural and semantic validation; review unknown safety gates and v1 boundary.
- `changes/`, `tools/change_contracts.py`: bounded scope; review base and actual diff handling.
- `tools/evidence.py`, `scripts/run-checks.sh`, `scripts/run-ros-checks.sh`,
  `.github/workflows/ci.yml`: shared commands, JUnit preservation, candidate versus tested SHA.
- `.agents/skills/robotics-*`, `.opencodereview/`, `tools/ocr_review.py`:
  bounded roles and optional read-only review; OCR execution remains unverified.
- `.github/pull_request_template.md`, `.github/ISSUE_TEMPLATE/`,
  `docs/reference/github-delivery-gates.md`: review handoff and proposed server rollout.

## Remaining merge gates and uncovered behavior

1. Review final diff from trusted base, including the checker and its own tests, against
   the ChangeContract. A candidate's self-check is insufficient to approve changed policy.
2. Push only after authorization, rerun fresh GitHub offline and Jazzy jobs, and inspect
   uploaded manifests, raw logs, and JUnit against the final candidate and tested merge SHA.
3. Verify OCR version, rule resolution, and changed-file preview before claiming an OCR
   review. Record each finding and its disposition; do not equate silence with approval.
4. Run a separate Agent behavior evaluation before claiming that Skills reliably block
   unsafe or out-of-scope actions. Fixture validation alone cannot prove it.
5. Apply and test required PR/check rules only as a separately authorized remote change.
   The repository template setting also remains disabled at the read-only baseline.

No hardware, physical output, localization, navigation, real sensor, braking, or independent
physical stop behavior was tested. The simulation result is bounded to fake ROS nodes.
