# Working Memory

## Objective

Provide a public, model-free AI design workflow for controlled indoor wheeled robots. The workflow produces a reviewable DesignPackage; it does not certify safety, recommend products, or authorize physical actuation.

## Current Status

Verified: v0.2 provides versioned design contracts, five focused Skills, synthetic examples, deterministic evaluation cases, and public-content safety checks.

## Evidence

- `contracts/` defines the v1 DesignBrief and DesignPackage boundary.
- `.agents/skills/` contains the ordered design workflow.
- `examples/` and `evals/` contain synthetic positive and safety-blocking cases.
- Full local verification: contract, Skill, evaluation, public-content, unit, Python, YAML, Markdown, and shell checks passed.

## Decisions

ADR-0001 selects versioned JSON contracts, model-free public outputs, ROS 2 reference architecture, and simulation-first safety gates.

## Blockers

Real robot requirements, calibration, electrical design approval, and physical trial authorization remain project-specific and must stay outside this public template.

## Next Actions

1. Copy a synthetic DesignBrief and replace it with verified local facts. Verify: brief validation passes.
2. Run the five Skills in order. Verify: completed DesignPackage validation passes.
3. Review project-specific risks and plan simulation evidence. Verify: verification plan names evidence and human gates.

## Verification

Run `scripts/run-checks.sh` in a POSIX shell, then run repository lint checks. Do not claim a physical safety result from a template or simulation check.

## Risks

- AI output can contain unsupported assumptions; preserve them as inferred or open items.
- Passing validation proves contract completeness, not algorithm performance or safety.
- Public artifacts must remain free of credentials, private infrastructure, customer data, and hardware identities.
