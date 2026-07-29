---
name: mobile-robot-verification-plan
description: Turn a model-free indoor wheeled robot DesignPackage into unit, integration, simulation, replay, and human safety-review evidence plans. Use when an AI needs acceptance criteria and failure-injection coverage before a mobile robot progresses beyond design.
---

# Mobile Robot Verification Plan / 移动机器人验证计划

Read `references/evidence-ladder.md` and `assets/verification-plan-template.md`. Use the completed DesignPackage as input.

## Workflow / 工作流

1. Map every interface, algorithm prerequisite, hardware degradation, and safety invariant to a narrowest useful check.
2. Define deterministic unit checks for bounds, units, request expiry, and state transitions.
3. Define integration checks with fake transports, then simulation and replay checks with synthetic data and injected failures.
4. Define a human safety review gate before a physical trial. Do not schedule or authorize a physical trial.
5. State measurable acceptance criteria and evidence artifacts for each check. Preserve untestable conditions as blockers.
6. Write the `verification_plan` section of the DesignPackage.

## Safety and public boundary / 安全与公开边界

- Prefer synthetic data, simulation, and replay; never require customer data or physical hardware access.
- Do not claim a passing test certifies safety or authorizes operation.
- Keep test inputs free of product names, site identifiers, accounts, endpoints, and credentials.

## Completion / 完成条件

Each behavior has an acceptance criterion, an evidence artifact, and an identified test level.
