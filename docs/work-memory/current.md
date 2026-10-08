# Working Memory

## Objective

Provide a public, model-free AI design workflow and a simulation-only ROS 2 engineering starting point for controlled indoor wheeled robots. The workflow produces a reviewable DesignPackage; the executable package does not certify safety, recommend products, or authorize physical actuation.

## Current Status

As of 2026-10-08, PR #19 was merged into `main` at `837da9e`; PR #18 is also
marked merged. The main-push CI run `37752465109` failed in a PR-specific unit
assertion. Its isolated fix is open in PR #20 at `fa748e4`, with both PR jobs
passing; the owner has not reviewed it and explicitly requested no merge yet.
The local `codex/all-in-code-review-gate` branch starts from `837da9e` and adds
a deterministic review inventory and record check for an Agent's uncommitted
candidate. It does not include PR #20 or change ROS control behavior. The
independent Agent's read-only review found missing index-only paths, unbound
base/head evidence claims, and staged deletion left in the worktree; all three
were repaired in this local branch.
The older candidate notes below describe the development history, not current PR state.

Verified: v0.2 provides versioned design contracts, five focused design Skills, an optional public
architecture-research Skill, synthetic examples, deterministic evaluation cases, and public-content
safety checks. The current work adds a ROS 2 Jazzy simulation slice for the validated synthetic
`warehouse-tote` example, with a safety gate, fake base, synthetic fault inputs, and a separate
ROS runtime CI gate. The PR #18 acceptance worktree proposes DesignPackage v2 and a fail-closed
gate restart; four ROS tests and their JUnit links passed locally in Jazzy on that candidate.
The separate `codex/ai-delivery-chain` worktree proposes a bounded ChangeContract, shared
offline and ROS evidence, three delivery Skills, and optional read-only OCR review. Local
offline and Jazzy checks passed on this local candidate; fresh GitHub CI remains
pending. This is a starting point, not a complete navigation system.
The follow-on local `codex/agent-requirement-delivery` branch routes a plain-language
development request through code generation, checks, a read-only review pass, bounded
fixes, and final evidence. A plan-phase contract can now reference planned test IDs;
the final gate still requires implemented tests. This is repository guidance for an
AGENTS.md-aware Agent, not an unattended model service.
The follow-on `codex/hardware-protocol-handoff` candidate defines a private,
source-backed hardware selection handoff, protocol-pending algorithm work over fake
interfaces, later received-protocol adapter checks, and a separate supervised physical
trial gate. It does not select a product, implement a driver, or authorize a trial.
An independent Agent reviewed this candidate and identified stale safety-state
recovery, self-selected ChangeContract baseline, and a historical contract-test
fixture that blocked new design work. The fixes are in the local candidate. A
separate Agent's first natural-language coding probe implemented a simulated
timeout diagnostic but remained BLOCKED by that historical fixture. A fresh
isolated rerun passed local offline and Jazzy checks. Its feature remains in
the isolated test clone and is not part of this candidate.

## Evidence

- `contracts/` defines the v1 DesignBrief and proposed v2 DesignPackage boundary.
- `.agents/skills/` contains the ordered design workflow.
- `open-source-architecture-research` inspects public project facts, ranks public candidates, and
  records evidence without copying code or using credentials.
- `examples/` and `evals/` contain synthetic positive and safety-blocking cases.
- `src/robotics_sim/` implements only simulated motion and publishes synthetic odometry.
- PR #18 baseline `1b23621`: 33 offline unit tests passed; Ruff, YAML, Markdown, shell, and public-content checks passed.
- PR #18 baseline Jazzy CI: `colcon build --packages-select robotics_sim` passed; two ROS graph and installed-launch tests passed with JUnit results and `colcon test-result` showing 2 tests, 0 failures.
- Acceptance worktree: 40 offline unit tests, four local Jazzy ROS tests, JUnit trace validation,
  and repository CI lint scopes passed. The exact results and remaining merge gates are in
  `docs/acceptance/pr18-engineering-acceptance.md`.
- AI delivery candidate: 51 offline unit tests, contract and public-content checks, Ruff,
  YAML, Markdown, ShellCheck, four Jazzy ROS tests, and JUnit requirement links passed
  locally. Raw logs and manifests are in ignored `artifacts/`; the candidate report is
  `docs/acceptance/ai-delivery-chain.md`. These results do not establish remote CI status.
- Requirement-to-code candidate: 53 offline unit tests, Skills and contract checks,
  lint, and four Jazzy simulation tests passed locally. The plan/final regression uses
  a real planned warehouse-tote requirement and test. A positive Agent workflow case
  is defined but has not been run with a separate Agent; self-review is not independent.
- Hardware/protocol handoff candidate: 54 offline unit tests and four Jazzy simulation
  tests passed locally. Git-ignore regression confirms a local private selection file
  is permitted while a force-tracked private file is rejected. The staged workflow
  acceptance record is `docs/acceptance/hardware-protocol-handoff.md`.
  Intermittent installed-launch reset rejection and missing first odometry exposed
  fixed-wait test races during ROS discovery; the test now waits boundedly for healthy
  simulated inputs and actual fake-base output. It passed three targeted reruns.
  The safety-gate runtime and physical-output state were not changed.
- Independent review follow-up: 56 offline unit tests, contract/public checks,
  Ruff, YAML, Markdown, and ShellCheck passed. Four Jazzy simulation tests,
  including synthetic safety-status loss and reset, passed. This is local
  evidence; independent human review remains outstanding.
  Independent follow-up found that a PR's fork base can differ from the next
  main push's prior tip. The push gate now checks all paths against the trusted
  event range while accepting an older contract base that precedes that tip.
- Independent Agent evaluation: the second natural-language coding probe on
  `0e31a22` produced a read-only simulated timeout topic, passed 57 offline
  unit tests and five Jazzy ROS tests, and recorded a self-review. Separate
  reviewer inspection of the candidate fixes found no remaining confirmed
  issue. A negative hardware-output probe correctly stopped for missing
  protocol, limits, safe procedure, and responsible approval. See
  `docs/acceptance/independent-agent-evaluation.md`.
- Installed launch smoke: three `/sim` nodes appeared, installed `max_linear_mps` resolved to 0.6, and `/sim/cmd_safe` published zero at rest.
- GitHub Actions for PR #18 at `1b23621`: `validate-template` and `ros2-simulation` passed; the ROS job reported 2 tests and 0 failures.
- PR #19 on `codex/hardware-protocol-handoff`: its first remote run exposed a
  Python executable alias mismatch in offline evidence validation and Git
  ownership protection in the ROS container. Workflow commit `2a920c6`
  corrected both. Run `37749992397` passed both jobs; uploaded manifests
  share PR merge-test SHA `6e0f22a` and snapshot digest `830a7ce2`, and its
  JUnit artifact has four cases with zero failures, errors, or skips.

## Decisions

ADR-0001 selects versioned JSON contracts, model-free public outputs, ROS 2 reference architecture, and simulation-first safety gates.
ADR-0003 records the simulation runtime scope and reference-project evidence boundary.
ADR-0004 proposes the versioned DesignPackage v2 upgrade and bidirectional trace requirement.
ADR-0005 proposes bounded changes and execution evidence, with `jsonschema` as a
development validator dependency and optional read-only OCR review.
ADR-0006 proposes a private hardware selection and protocol intake boundary while
preserving the model-free public DesignPackage and physical-output gate.

## Blockers

Real robot requirements, localization, navigation, sensor integration, calibration, electrical design approval, and physical trial authorization remain project-specific and must stay outside this public template until independently specified and verified.
PR #20 remains unmerged pending the owner's independent review; `main` CI stays
red for that known test assertion. This new local branch also requires independent
human review of its validator and test changes, plus future remote CI on its final
candidate head before merge. OCR CLI is not installed here, so no OCR model review
is claimed. GitHub ruleset and repository-template settings were not changed.
No project-specific hardware requirements, selected device, received protocol,
calibration, electrical approval, or physical-trial authorization exists in this
template. An independent human reviewer and final-head remote CI remain
merge gates for this candidate.

## Next Actions

0. Finish the local review-record validator regression, offline and Jazzy gates,
   then retain snapshot-bound evidence and independent Agent findings. Do not
   merge PR #20 or this branch without a separate owner decision.
1. Copy a synthetic DesignBrief and replace it with verified local facts. Verify: brief validation passes.
2. When selecting a new architecture, run public reference research and review sources and licenses.
   Verify: a local recommendation names evidence, open decisions, and a verification step.
3. Run the five Skills in order. Verify: completed DesignPackage validation passes.
4. Extend the synthetic ROS graph only from validated project requirements. Verify: offline logic, real ROS graph, and installed launch checks cover each new behavior.
5. Review project-specific risks and plan simulation evidence before any physical trial. Verify: the verification plan names evidence and human gates.
6. Have an independent human inspect the core-chain candidate diff and fresh
   GitHub CI evidence before considering a merge. Verify: approved tests and
   review findings refer to the final proposed commit and uploaded artifacts.
7. For a new hardware-dependent project requirement, build a private selection list
   linked to public requirement and interface IDs, and implement independent algorithm
   behavior with fake or replay transport. Verify source dates and unresolved gaps.
8. After protocol receipt, reconcile the exact revision and produce reviewed adapter
   tests before requesting a separately authorized stationary physical procedure.

## Verification

Run `bash scripts/run-checks.sh` and, on a Jazzy host, `bash scripts/run-ros-checks.sh`.
These scripts create snapshot-bound manifests and raw logs. Validate each manifest with
`python3 tools/evidence.py validate artifacts/<run-id>`. Do not claim a physical safety
result from a template or simulation check.

## Risks

- AI output can contain unsupported assumptions; preserve them as inferred or open items.
- Passing validation proves contract completeness, not algorithm performance or safety.
- Public artifacts must remain free of credentials, private infrastructure, customer data, and hardware identities.
- The fake base has ideal kinematics and no measured braking, sensing, timing guarantee, or independent physical stop path.
