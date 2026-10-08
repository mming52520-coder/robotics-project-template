---
name: mobile-robot-control-safety
description: Define control authority, bounded motion requests, stop behavior, watchdogs, fault recovery, and simulation-to-hardware gates for a controlled indoor wheeled robot. Use when reviewing or designing a mobile-robot safety plan before any physical actuation is considered.
---

# Mobile Robot Control Safety / 移动机器人控制安全

Read `references/control-safety-invariants.md` and `assets/safety-plan-template.md`. Require a validated DesignBrief before proceeding.

## Workflow / 工作流

1. Confirm that emergency stop, speed limit, and physical-output state are defined. Stop with blockers when any is unknown.
2. Define one control-authority path from mission or operator requests through a safety gate to the base interface.
3. Define bounds, freshness expiry, stop behavior, watchdog behavior, diagnostics, and fault recovery. A stale or invalid command resolves to zero motion.
4. Define the simulation, fake-transport, and documented physical-trial gates. Keep hardware output disabled unless a responsible human authorizes a safe procedure.
   Protocol receipt and passing adapter tests do not open that gate. Require a separate
   human-reviewed stationary bring-up and bounded trial procedure with verified stop,
   interlock, limits, watchdog, fault handling, and a named abort owner.
5. Write the `safety_plan` section of the DesignPackage.

## Safety and public boundary / 安全与公开边界

- Never generate executable motion commands, disable an interlock, or weaken a stop condition.
- Treat the design as an engineering aid, not a functional-safety certificate.
- Keep all real device configuration, site data, and credentials outside public outputs.

## Completion / 完成条件

The plan names a single safety gate, explicit zero-motion conditions, watchdog expiry, reset prerequisites, and a human review gate.
