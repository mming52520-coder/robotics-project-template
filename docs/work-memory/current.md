# Working Memory

## Objective

Provide a public, model-free AI design workflow and a simulation-only ROS 2 engineering starting point for controlled indoor wheeled robots. The workflow produces a reviewable DesignPackage; the executable package does not certify safety, recommend products, or authorize physical actuation.

## Current Status

Verified: v0.2 provides versioned design contracts, five focused design Skills, an optional public
architecture-research Skill, synthetic examples, deterministic evaluation cases, and public-content
safety checks. The current work adds a ROS 2 Jazzy simulation slice for the validated synthetic
`warehouse-tote` example, with a safety gate, fake base, synthetic fault inputs, and a separate
ROS runtime CI gate. This is a starting point, not a complete navigation system.

## Evidence

- `contracts/` defines the v1 DesignBrief and DesignPackage boundary.
- `.agents/skills/` contains the ordered design workflow.
- `open-source-architecture-research` inspects public project facts, ranks public candidates, and
  records evidence without copying code or using credentials.
- `examples/` and `evals/` contain synthetic positive and safety-blocking cases.
- `src/robotics_sim/` implements only simulated motion and publishes synthetic odometry.
- Offline `scripts/run-checks.sh`: 33 unit tests passed. Ruff, YAML, Markdown, shell, and public-content checks passed.
- Jazzy container: `colcon build --packages-select robotics_sim` passed; two ROS graph and installed-launch tests passed with JUnit results and `colcon test-result` showing 2 tests, 0 failures.
- Installed launch smoke: three `/sim` nodes appeared, installed `max_linear_mps` resolved to 0.6, and `/sim/cmd_safe` published zero at rest.

## Decisions

ADR-0001 selects versioned JSON contracts, model-free public outputs, ROS 2 reference architecture, and simulation-first safety gates.
ADR-0003 records the simulation runtime scope and reference-project evidence boundary.

## Blockers

Real robot requirements, localization, navigation, sensor integration, calibration, electrical design approval, and physical trial authorization remain project-specific and must stay outside this public template until independently specified and verified. ROS 2 CI has run locally in a Jazzy container; the remote GitHub Actions result for the proposed change is pending.

## Next Actions

1. Copy a synthetic DesignBrief and replace it with verified local facts. Verify: brief validation passes.
2. When selecting a new architecture, run public reference research and review sources and licenses.
   Verify: a local recommendation names evidence, open decisions, and a verification step.
3. Run the five Skills in order. Verify: completed DesignPackage validation passes.
4. Extend the synthetic ROS graph only from validated project requirements. Verify: offline logic, real ROS graph, and installed launch checks cover each new behavior.
5. Review project-specific risks and plan simulation evidence before any physical trial. Verify: the verification plan names evidence and human gates.

## Verification

Run `scripts/run-checks.sh` and repository lint checks. For ROS 2, build with Jazzy, source the installed workspace, run `python3 -m pytest -q src/robotics_sim/test/test_*.py`, and inspect `colcon test-result`. Do not claim a physical safety result from a template or simulation check.

## Risks

- AI output can contain unsupported assumptions; preserve them as inferred or open items.
- Passing validation proves contract completeness, not algorithm performance or safety.
- Public artifacts must remain free of credentials, private infrastructure, customer data, and hardware identities.
- The fake base has ideal kinematics and no measured braking, sensing, timing guarantee, or independent physical stop path.
