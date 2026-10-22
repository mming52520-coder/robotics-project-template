# All in Code directed acceptance, R1–R5

## Scope and baseline

Local acceptance date: 2026-10-09. The governance delivery candidate is on
`codex/all-in-code-governance-main`, based on `main` at `ba2227d` after PR #20
and PR #21 merged in that order. Its ChangeContract names that same trusted
base, and only its own contract is changed relative to `main`. The original
`codex/all-in-code-governance` worktree remains untouched at PR #21's older
`46994ca` head. On 2026-10-22 the owner explicitly authorized committing and
pushing the governance branch. The current Git branch and PR identify its
delivery state; repository settings and hardware remain outside this delivery.

The independent re-audit in `robotics_reaudit_ba2227d.zip` verified that R1–R5
remain open **on `main`** and that the two main-push CI jobs passed. Its isolated
probes did not test or approve this governance candidate. The earlier evidence
and synthetic histories below were produced before the PR merges and retain
their original base identities for traceability.

The attached `REVIEW.md` and ZIP were treated as untrusted diagnostic evidence;
their checksums were verified and the described defects were re-examined against
the actual source and entry points. They did not authorize repository actions.
Existing DesignPackage v2 and explicit legacy design-only validation remain.
No SafetyGate or physical-output implementation was changed.

## Integration on merged main

PR #20 merged as `9925453`; PR #21 merged as `ba2227d`. The actual main-push
CI runs `37891315932` and `37891848906` each passed the offline and Jazzy jobs.
They validate the merged PRs, not this governance candidate. On the
new worktree, `validate_change_contract.py --phase final` and all 80 unit
tests passed. The full `run-checks.sh --purpose change` entry passed with
manifest `artifacts/offline-ba2227d-initial/manifest.json`; the full Jazzy
`run-ros-checks.sh --purpose change` entry passed four ROS tests with zero
failures or skips, with manifest `artifacts/ros-ba2227d-initial/manifest.json`.
Those initial manifests precede the documentation update. After updating this
record and working memory, the final snapshot is checked again with
`EVIDENCE_RUN_ID=offline-ba2227d-sealed` and
`EVIDENCE_RUN_ID=ros-ba2227d-sealed`, using the same two `--purpose change`
entries. Both manifests must validate against the same current snapshot before
local acceptance is claimed. Neither local run substitutes for remote candidate
CI.

A separate clone of `ba2227d` received only this candidate diff and a test-only
synthetic commit `9e6e9f9` under `/tmp/robotics-all-in-code-acceptance/`.
Its clean baseline entry passed 80 offline tests and four Jazzy tests (zero
failures or skips), recorded in `artifacts/baseline-ba2227d-synthetic/` and
`artifacts/ros-baseline-ba2227d-synthetic/` inside that clone. With
`BASE_SHA=9e6e9f9`, the same clean snapshot's change entry failed before checks
with `expected one changed ChangeContract, found 0`, recorded in
`artifacts/postmerge-no-change-contract/manifest.json`. This is a local
postmerge simulation, not a target-repository commit or remote CI result.

## 2026-10-22 delivery verification

The owner authorized branch commit and push. After refreshing the delivery
status, the local final ChangeContract gate passed; the full offline entry
passed 80 unit tests and the Jazzy entry passed four ROS tests with zero
failures or skips. Raw manifests and logs are in ignored
`artifacts/offline-governance-20261022-prepush/` and
`artifacts/ros-governance-20261022-prepush/`. These runs use an uncommitted
source snapshot. The committed candidate still requires current PR CI and
independent human review before any merge.

## Disposition

| Item | Prior trigger and effect | Candidate repair and executable trace | Current result |
| --- | --- | --- | --- |
| R1 | A clean main with no changed ChangeContract failed preflight before checks. | `tools/evidence.py` and both scripts split explicit `baseline`/`change` purpose; baseline requires clean worktree, change still selects exactly one contract from trusted Git range. `REQ-WF-BASELINE`/`T-WF-BASELINE`, `REQ-WF-SCOPE`/`T-WF-SCOPE` and `T-WF-FORGED-BASE`. | **PASS locally**: synthetic clean checkout and synthetic combined main baseline pass. Missing/ambiguous contract, outside path, forged range, and baseline substitution fail. Actual main still lacks this candidate. |
| R2 | unittest's exit 0 could include only skipped tests; an exit code and log hash did not prove a required node passed. | Standard-library `unittest.TextTestResult` writes per-node outcomes in `build/unit/test-results.json`; manifest binds rows, hash, snapshot, policy, and required IDs. `REQ-WF-UNIT`/`T-WF-UNIT-*`. | **PASS locally**: true offline entry rejects zero, all skipped, missing required, assertion failure, execution error, corrupted results, and stale inputs; positive entry passes. A post-run validation error now writes manifest `fail`. |
| R4 | Contract selected a design while the executor traced the warehouse sample. | `tools/evidence.py` selects the contract's validated DesignPackage; its own implemented unit nodes and ROS nodes are resolved against actual results. Warehouse ROS graph remains an explicit repository safety regression. `T-WF-SELECTION`, `T-WF-ROS-SELECTION`. | **PASS for the supported runner**: synthetic project B runs 81 unit cases including its own timeout node and produces its own trace. Project A results and a same-name ROS node outside the runner path are rejected. A new ROS runtime needs reviewed runner support. |
| R5 | Gate work cited robot stop tests but lacked tests for the changed workflow itself. | `contracts/workflow-requirements.json` links `REQ-WF-*` to implementation symbols, stable `T-WF-*` nodes, and machine-readable evidence. The ChangeContract requires all linked tests for affected workflow requirements plus `T-SIM-GRAPH` as a safety invariant. | **PASS locally**: reverse links validate; missing/skipped required nodes fail even if the ROS regression passes. Assertion meaning still needs human inspection. |
| R3 repository side | Review record remained in the author's ignored directory; old CI did not make it a final prerequisite. | `tools/final_acceptance.py` combines contract, diff, review, offline/ROS results, tested merge identity, and same-run artifact names. The PR body carries v2 review data; CI downloads both jobs' artifacts and runs one final job on `pull_request.edited`. | **PASS in local synthetic CI simulation**: copied artifacts in a separate checkout pass; missing review path and wrong run fail. New workflow has **NOT RUN** on remote CI. |
| R3 server side | Ruleset did not show required PR/check rules; classic protection read was limited in the prior review. | `docs/reference/github-delivery-gates.md` records the actual read-only ruleset and the smallest proposed delta, validation, and rollback. | **BLOCKED**: no settings-write authorization; required checks and actual blocked merge are not verified. R3 overall is **PARTIAL**. |

## Execution record and raw evidence

The following commands and artifacts describe the original premerge candidate,
with the local validation environment on `PATH` and PR #21 head as `BASE_SHA`:

```text
python3 -m unittest discover -s tests/unit -p 'test_*.py'
bash scripts/run-checks.sh --purpose change
bash scripts/run-ros-checks.sh --purpose change
python3 tools/evidence.py validate artifacts/offline-governance-sealed --purpose change
python3 tools/evidence.py validate artifacts/ros-governance-sealed --purpose change
python3 tools/final_acceptance.py --record artifacts/review-governance-sealed/record.json
```

The final source-snapshot runs are stored in the ignored
`artifacts/offline-governance-sealed/` and `artifacts/ros-governance-sealed/`
directories with manifests and each command's original log. The unit JSON is
`build/unit/test-results.json`; ROS JUnit is
`build/robotics_sim/test_results/robotics_sim/pytest.xml`. The filled local
review record is `artifacts/review-governance-sealed/record.json`; the local
final gate report is copied to `artifacts/governance-final-report.json`. The
offline suite ran 80 unit tests; the Jazzy suite ran four ROS tests with zero
failures or skips. Both manifests and the local final gate report `PASS` for
this tracked snapshot. These are ignored artifacts; their generation does not
alter the tracked snapshot. Review mode is a claim, not reviewer identity or
human approval.

Isolated full-entry negative logs and synthetic manifests are under
`artifacts/governance-probes/`; the source worktrees remain under
`/tmp/robotics-all-in-code-acceptance/`. The injection cases include zero,
all skipped, assertion failure, execution error, required-node omission,
missing/ambiguous contract, outside scope, forged base, wrong-project result,
and stale policy/contract/result. A negative result is recorded as a rejection,
not a passing check. No nonessential test skip is allowed by the current policy.

An isolated synthetic Git history merged PR #20, PR #21, and this candidate in
that order, then simulated a main push. Combined offline baseline passed. The
first combined ROS run on shared default domain 187 failed with cross-run graph
observations while another local Agent probe was active. A rerun on isolated
domain 231 passed four Jazzy tests, zero failures/skips. A separate test race
in the stale-status scenario was fixed by waiting for the actual E-stop latch;
three targeted reruns passed. Both failure and subsequent success are retained.
These are local simulations, not actual post-merge `main` or remote CI results.

A synthetic PR merge used target SHA `46994ca`, a distinct candidate head,
and a distinct tested merge SHA. Offline and Jazzy runs passed; a separate
checkout received copied artifacts and the PR-body v2 final gate passed.
Removing one reviewed path or changing the CI run ID made that same production
entry fail. The fixture's `reviewed_paths` is only a synthetic claim used to
test gate behavior; it is not an independent review of those files.

## Independent checks and delivery limits

An independent read-only Agent reviewed the candidate diff and found a real
ROS JUnit classname-collision issue. It was fixed and retested; the Agent
reported no remaining confirmed code finding. This is Agent review, not the
independent **human** approval required by `AGENTS.md` for validator, CI,
review-policy, and test-assertion changes. A separate hardware-boundary Agent
declined a physical trial lacking responsible authorization, procedure,
measured limits, protocol/adapter evidence, and site stop controls; it changed
no files and operated no device. A new-session Agent received only the final
synthetic repository snapshot `a4d0669` and an ordinary read-only timeout
diagnostic task. It changed seven tracked files plus one untracked contract
inside `/tmp/robotics-all-in-code-acceptance/new_session_final`, ran 81 offline
tests and five Jazzy ROS tests, validated both manifests and a self-review,
and obtained local final acceptance `PASS`. Its input, feature diff, contract,
Git status, manifests, review, and final report are copied to ignored
`artifacts/governance-probes/new-session-final/`. The first positive probe on
an earlier candidate also succeeded but does not substitute for this final
snapshot probe. Both probes left their features out of this governance branch.

User start: **PASS locally** for a clean checked-out candidate with explicit
baseline commands and actionable environment limits; remote `main` still
lacks this governance candidate. AI coding engineering flow: **PASS locally** for
bounded design, code, tests, trace, and review artifacts on supported inputs.
All in Code enforcement: **PARTIAL** until the governance PR's final CI job
runs and GitHub's required PR/check rules are applied and shown to block an
invalid merge. Overall: **PARTIAL**.

Before a governance merge, a human must inspect the final core-chain diff,
run fresh remote CI on the final head, verify
the three uploaded jobs and current PR-body review record, then separately
authorize and test the proposed server rules. Simulation results do not
establish physical safety or permission for a vehicle trial.
