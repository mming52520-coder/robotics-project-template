# PR #18 engineering acceptance — 2026-10-08

## Verdict

**NO-GO for merge at this point.** The local candidate passes the available offline
contract, unit, lint, local Jazzy simulation, and JUnit evidence gates. The candidate has not
been pushed, so its GitHub CI has not run; the original PR's successful CI applies only to its
unchanged head. A reviewer still needs to approve the v2 migration and inspect a fresh CI run.
No physical hardware or physical output was used.

## Read-only baseline

| Item | Observed fact |
| --- | --- |
| Repository and PR | `mming52520-coder/robotics-project-template`, [PR #18](https://github.com/mming52520-coder/robotics-project-template/pull/18), open and unmerged |
| Base | `main` at `94bd7933274bf00ece36e57bb8d78cfd4cd60594`; original checkout clean |
| PR head | `codex/ros2-simulation-foundation` at `1b23621273141a4f3499ebbc25be5491d6bae5b5` |
| PR diff | 23 files, 725 additions, 12 deletions; no changes to the v1 contract validator or schema |
| Existing CI | [run 37722347978](https://github.com/mming52520-coder/robotics-project-template/actions/runs/37722347978): `validate-template` and `ros2-simulation` succeeded at the PR head |
| Existing ROS evidence | CI log reports 2 pytest cases and `colcon test-result` summary of 2 tests, 0 failures; uploaded `ros2-simulation-logs` contains `log/` files but no JUnit XML |
| Candidate | Independent `codex/pr18-engineering-acceptance` worktree from PR head; local branch, not pushed; main and PR head unchanged |

Baseline defects and risks:

1. **FAIL — v1 false acceptance.** With `interfaces=[{}]`, `algorithm_plan=[{}]`,
   `hardware_functional_plan=[{}]`, and `verification_plan={}`, the original
   `validate_design_package` returned `[]`. Required units, frame, freshness, failure
   behavior, acceptance, and evidence therefore had no hard gate.
2. **FAIL — restart latch.** `SafetyGate.__init__` set `estop_latched=False`; a restarted
   safety-gate process could accept a new request after synthetic status messages resumed
   without an explicit reset. No baseline test covered that transition.
3. **RISK — execution claim.** ADR-0003 said `colcon test` ran, while CI actually used
   direct `python3 -m pytest` followed by `colcon test-result`. The original upload omitted
   the JUnit file, so its two cases cannot be inspected as an attached artifact.
4. **RISK — simulation limit.** The fake base can retain the last safe command for its
   independent 0.2 s timeout if the gate process dies. No measured stopping time or
   physical safety conclusion is available.

## Candidate change and trace boundary

The v1 DesignBrief is retained. `contracts/design-package.schema.json` and
`tools/design_contracts.py` now require DesignPackage v2; all three public packages are
explicitly migrated. The validator checks nonempty typed interfaces, algorithm and hardware
plans, safety and verification plans, finite known bounds, source pointers, exact reverse
links, repository source symbols, and test node IDs. Unknown safety values block completion.
`tools/validate_design_package.py --evidence` additionally requires a passing JUnit case
for every implemented check. These checks verify trace integrity, not functional safety.

| Requirement | Design IDs | ROS behavior and implementation | Test IDs | Evidence |
| --- | --- | --- | --- | --- |
| `REQ-SIM-BOUND` | `IF-SIM-REQUEST`, `IF-SIM-SAFE`, `SAFE-SIM` | bounded `/sim/cmd_request` through `SafetyGate.receive_command` and `SafetyGateNode._command` | `T-SIM-GRAPH` | Jazzy pytest JUnit |
| `REQ-SIM-STOP` | `IF-SIM-SAFE`, `SAFE-SIM` | zero on stale status or command through `SafetyGate.output`; independent `FakeBase.step` expiry | `T-SIM-START`, `T-SIM-GRAPH` | Jazzy pytest JUnit |
| `REQ-SIM-ESTOP` | `IF-SIM-ESTOP`, `IF-SIM-RESET`, `SAFE-SIM` | latch and guarded reset in `SafetyGate.receive_estop` and `reset_estop` | `T-SIM-GRAPH`, `T-SIM-RESTART`, `T-SIM-PROC-RESTART` | Jazzy pytest JUnit |
| `REQ-SIM-FAULT` | `IF-SIM-HEALTH`, `IF-SIM-OBSTACLE`, `SAFE-SIM` | clear command on synthetic health and obstacle faults | `T-SIM-GRAPH` | Jazzy pytest JUnit |
| `REQ-SIM-RESTART` | `IF-SIM-RESET`, `SAFE-SIM` | constructor starts latched; in-process and separate-process restart tests | `T-SIM-RESTART`, `T-SIM-PROC-RESTART` | Jazzy pytest JUnit |
| `REQ-SIM-FAKE` | `IF-SIM-ODOM`, `SAFE-SIM` | `FakeBase.step` and `FakeBaseNode._step` publish synthetic odometry only | `T-SIM-START`, `T-SIM-GRAPH` | Jazzy pytest JUnit |

The exact source pointers, ROS interfaces, source files, test node paths, and shared artifact
`build/robotics_sim/test_results/robotics_sim/pytest.xml` are in
`examples/warehouse-tote/design-package.json`. Planned localization, navigation, and
functional hardware requirements have planned checks and no invented implementation evidence.

## Acceptance results

| Gate | Result | Evidence and limit |
| --- | --- | --- |
| PR/base/worktree identity and no merge | **PASS** | Git and GitHub read-only inspection; branch is separate from main and PR head |
| v1 defect reproduction | **FAIL at baseline** | Malformed package returned no errors under original validator |
| v2 structure, missing/null/type, unknown thresholds | **PASS offline** | 3 migrated examples, negative unit tests, independent Draft 2020-12 schema check |
| Bidirectional static trace | **PASS offline** | All six implemented requirements resolve design, ROS name, source symbol, and test node; broken links fail unit tests |
| JUnit result to requirement link | **PASS locally** | Actual Jazzy JUnit has four passing cases; `--evidence` resolved every implemented check |
| Launch and zero output at rest | **PASS locally** | Installed `sim.launch.py` started the three `/sim` nodes and published zero at rest |
| Bounded command and rejected invalid request | **PASS locally** | Core negatives and ROS graph rejected an out-of-bounds command; other unused Twist axes are checked in the adapter but not exercised by ROS test |
| Stop and command/status timeout | **PASS locally** | Core command/status expiry, graph command expiry and zero odometry, and separate-process fake-base expiry after gate stop |
| Emergency-stop latch and guarded reset | **PASS locally** | Startup, asserted/cleared emergency stop, reset and fresh-command requirement in graph and core tests |
| Synthetic health/obstacle faults | **PASS locally** | Both faults clear prior motion in core and ROS graph tests; no physical sensor fault was injected |
| Gate restart fail-closed | **PASS locally** | Constructor, in-process recreation, and separate-process restart all require explicit reset |
| Candidate GitHub CI and uploaded JUnit | **BLOCKED** | Local branch has not been pushed; old PR run does not cover these changes |
| Physical stop, braking, sensor validity, field timing | **BLOCKED/out of scope** | No hardware, measured dynamics, independent physical stop path, or authorized physical test |

The local ROS run used `ROS_DOMAIN_ID=187` and localhost discovery. The process-restart test
observes synthetic odometry return to zero after gate exit and verifies the new gate remains
at zero until safe reset. This does not measure a real robot's stopping time or guarantee a
hard real-time deadline. Candidate results come from this local worktree, never from old CI.

## Command log

The full local command output is preserved alongside this report as
`pr18-acceptance-command-log.txt`. Key commands and observations:

| Command | Result |
| --- | --- |
| `gh pr view 18 --repo mming52520-coder/robotics-project-template --json ...` | Open, unmerged, head `1b23621`, clean merge status, both CI jobs successful on that head |
| `git diff --check origin/main...origin/pr-18` | PASS; original PR diff has no whitespace errors |
| `PATH="$PWD/.venv/bin:$PATH" bash scripts/run-checks.sh` on PR head | PASS; 33 unit tests |
| Baseline malformed-package reproduction | FAIL as intended; original validator returned `[]` |
| `PATH="$PWD/.venv/bin:$PATH" bash scripts/run-checks.sh` on candidate | PASS; 40 unit tests, template/Skill/evaluation/public-content checks |
| `python tools/validate_design_package.py` on all three v2 pairs | PASS |
| `Draft202012Validator.check_schema` and validate three examples | PASS; local verification tool only, no repository dependency added |
| `ruff`, `yamllint`, `pymarkdown`, `shellcheck`, `git diff --check` | PASS on the repository's CI scopes |
| `colcon build --packages-select robotics_sim` under local Jazzy | PASS; one package built |
| ROS pytest with actual JUnit | PASS; four cases in 10.12 s, 0 failures, 0 skipped |
| `validate_design_package.py --evidence` and `colcon test-result --verbose` | PASS; four linked cases, 0 errors/failures/skips |

An exploratory Ruff run across **all** `tests/unit` found two pre-existing import-order
violations outside the CI scope. No unrelated test files were changed; the modified contract
test was added to the CI Ruff scope.

## Review locations and merge gates

| Area | Files |
| --- | --- |
| v2 contract and links | `contracts/design-package.schema.json`, `tools/design_contracts.py`, `tools/validate_design_package.py`, `examples/*/design-package.json` |
| Contract and safety negatives | `tests/unit/test_design_contracts.py`, `tests/unit/test_sim_core.py` |
| ROS behavior | `src/robotics_sim/robotics_sim/core.py`, `src/robotics_sim/test/test_sim_graph.py`, `src/robotics_sim/test/test_installed_launch.py` |
| CI evidence | `.github/workflows/ci.yml` uploads JUnit XML and checks its passing cases |
| Migration and scope | `contracts/README.md`, `docs/decisions/0004-design-package-v2-traceability.md`, `docs/reference/ros2-simulation.md`, `README.md`, `docs/work-memory/current.md` |

Before merging, a reviewer must authorize publishing this candidate branch or reproduce the
same changes in an authorized branch, run the updated offline and Jazzy CI gates, inspect the
uploaded JUnit XML and all four ROS test cases, and review the v2 migration impact for external
DesignPackage users. Any failing or missing check remains a merge blocker. This report itself
does not authorize a merge or physical trial.
