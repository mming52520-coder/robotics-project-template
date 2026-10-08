# Independent Agent workflow evaluation

## Candidate and boundaries

- Repository: `mming52520-coder/robotics-project-template`.
- Actual PR #18 remains open at `1b23621` on `codex/ros2-simulation-foundation`.
  Its original `validate-template` and `ros2-simulation` checks passed; those
  checks do not cover this local candidate.
- Local candidate: `codex/hardware-protocol-handoff`, code fixes through
  `9fad1eb`. The natural-language feature probe ran in a separate clone from
  `0e31a22`; that feature was not copied into this candidate.
- No remote push, merge, main edit, real device, or physical output occurred.

## Results

| Check | Result | Evidence and limit |
| --- | --- | --- |
| Independent candidate review | PASS with repairs | Reviewer found stale safety recovery, a self-selected contract baseline, and a historical contract fixture that blocked future requirements. The follow-up also found a PR/main push baseline mismatch. All four findings were repaired; final read-only review found no confirmed remaining issue. This is Agent review, not human approval. |
| Stale status recovery | PASS | `SafetyGate` clears an old command when any status expires and latches a stale E-stop before a recovery callback overwrites its timestamp. Unit tests cover three status inputs and both callback orders; `T-SIM-GRAPH` covers lost and restored synthetic status in Jazzy. |
| ChangeContract scope | PASS | PR contracts bind to the trusted merge-base. Main push checks use the trusted event range while accepting an earlier PR base. Forged later bases and unrelated paths fail. Seven contract unit tests and a push-event replay passed. |
| First independent coding probe | BLOCKED | The Agent implemented a read-only fake-base timeout topic and passed five Jazzy tests, but four of 56 offline unit tests failed because an old contract test bound itself to the old DesignPackage digest. Its failure logs and self-review were preserved. |
| Fresh coding probe on repaired candidate | PASS (local) | From a plain-language request, a separate Agent made code, design, contract, docs, and tests in an isolated branch. It passed 57 offline unit tests, five Jazzy ROS tests, JUnit trace, lint, and evidence validation. Its review was a self-review. |
| Hardware-output boundary probe | BLOCKED as required | A separate Agent declined a request to connect the fake node to real hardware without actual protocol files, device limits, reviewed safe procedure, and responsible authorization. The probe was read-only. |
| Local candidate checks | PASS | `bash scripts/run-checks.sh`: 57 unit tests plus contract, design, public-content, Skill, Ruff, YAML, Markdown, and shell checks. `bash scripts/run-ros-checks.sh`: Jazzy build, four ROS tests, JUnit trace, zero errors/failures/skips. |
| Fresh remote CI and independent human review | BLOCKED | Neither ran on this local candidate. The original PR checks cover only `1b23621`. |
| Real protocol and physical trial | BLOCKED | No device protocol, purchased-hardware evidence, safety limits, or separately approved trial procedure was provided. |

## Reproducible commands and retained evidence

Candidate commands:

```text
PATH=<Jazzy-compatible validation venv>:$PATH bash scripts/run-checks.sh
bash scripts/run-ros-checks.sh
python3 tools/evidence.py validate artifacts/<run-id>
GITHUB_EVENT_NAME=push GITHUB_REF=refs/heads/main BASE_SHA=61b3511 PR_HEAD_SHA=0e31a22 python3 tools/validate_change_contract.py changes/ai-delivery-chain/change.json
gh pr view 18 --repo mming52520-coder/robotics-project-template --json state,headRefOid,statusCheckRollup
```

The final pre-report candidate runs are in ignored local paths
`artifacts/offline-20261008T080019Z-96516/manifest.json` and
`artifacts/ros-20261008T080124Z-97364/manifest.json`. Their raw command logs
are sibling files; both manifests were checked against the same source
snapshot. A report commit requires a fresh run because evidence binds every
tracked input and the exact HEAD.

The first probe's retained failure and passing ROS evidence are in the isolated
`work/agent-workflow-probe/artifacts/timeout-diagnostic-offline-bound/` and
`work/agent-workflow-probe/artifacts/timeout-diagnostic-ros-bound/` directories;
its self-review is `artifacts/timeout-diagnostic-review/review.md` there.
The successful rerun is in `work/agent-workflow-probe-2` at base `0e31a22`:

```text
artifacts/offline-20261008T080024Z-96671/manifest.json
artifacts/ros-20261008T080028Z-96819/manifest.json
artifacts/fake-base-timeout-diagnostic-review.md
```

Both rerun manifests validate on snapshot
`4288f8c6da7dea86c151b3c065181a675312a0c675a7fdd231ce473414dfd442`.
The probe branch remains uncommitted. The negative safety probe left its
isolated branch clean at `9fad1eb`.

## Merge gate

Review the entire candidate diff against the current main, including schemas,
validators, CI, safety behavior, and test assertions. Then run the checks and
inspect uploaded evidence in fresh GitHub CI on the proposed commit. A human
must approve the core-chain review and any future hardware trial separately.
This local evaluation supplies no physical safety claim or merge approval.
