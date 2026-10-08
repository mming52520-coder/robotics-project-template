# Working Memory

## Objective

Provide a public, model-free AI design workflow and a simulation-only ROS 2 engineering starting point for controlled indoor wheeled robots. The workflow produces a reviewable DesignPackage; the executable package does not certify safety, recommend products, or authorize physical actuation.

## Current Status

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
- Installed launch smoke: three `/sim` nodes appeared, installed `max_linear_mps` resolved to 0.6, and `/sim/cmd_safe` published zero at rest.
- GitHub Actions for PR #18 at `1b23621`: `validate-template` and `ros2-simulation` passed; the ROS job reported 2 tests and 0 failures.

## Decisions

ADR-0001 selects versioned JSON contracts, model-free public outputs, ROS 2 reference architecture, and simulation-first safety gates.
ADR-0003 records the simulation runtime scope and reference-project evidence boundary.
ADR-0004 proposes the versioned DesignPackage v2 upgrade and bidirectional trace requirement.
ADR-0005 proposes bounded changes and execution evidence, with `jsonschema` as a
development validator dependency and optional read-only OCR review.

## Blockers

Real robot requirements, localization, navigation, sensor integration, calibration, electrical design approval, and physical trial authorization remain project-specific and must stay outside this public template until independently specified and verified.
The acceptance worktree additionally requires fresh GitHub CI with uploaded JUnit evidence before merge.
The AI delivery candidate also needs trusted-base inspection of its validators, Schemas,
CI, review rule, and tests. OCR CLI and Agent behavior evaluation were not run locally;
GitHub ruleset and repository-template settings were not changed.

## Next Actions

1. Copy a synthetic DesignBrief and replace it with verified local facts. Verify: brief validation passes.
2. When selecting a new architecture, run public reference research and review sources and licenses.
   Verify: a local recommendation names evidence, open decisions, and a verification step.
3. Run the five Skills in order. Verify: completed DesignPackage validation passes.
4. Extend the synthetic ROS graph only from validated project requirements. Verify: offline logic, real ROS graph, and installed launch checks cover each new behavior.
5. Review project-specific risks and plan simulation evidence before any physical trial. Verify: the verification plan names evidence and human gates.

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
