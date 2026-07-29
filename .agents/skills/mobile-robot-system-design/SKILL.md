---
name: mobile-robot-system-design
description: Turn a validated DesignBrief into a model-free ROS 2 reference system design for a controlled indoor wheeled robot. Use when a user needs system boundaries, node responsibilities, data flow, interfaces, assumptions, or open decisions before implementing mobile-robot software or hardware.
---

# Mobile Robot System Design / 移动机器人系统设计

Read `contracts/design-brief.schema.json`, `references/system-design.md`, and `assets/system-design-template.md` before drafting a design.

## Workflow / 工作流

1. Validate the supplied DesignBrief with `python tools/validate_design_package.py BRIEF`.
2. Stop and list blockers when a critical safety value is unknown. Do not infer emergency-stop, speed-limit, or physical-output behavior.
3. Build a ROS 2 reference architecture with separate mission, state estimation, navigation, safety gate, diagnostics, and simulation/fake transport responsibilities.
4. Define each interface with producer, consumer, data, units, frame, freshness expectation, and failure behavior.
5. Record every non-observed statement as `inferred` or `open`; only mark a statement `confirmed` when the brief or supplied evidence supports it.
6. Write the `system_architecture`, `interfaces`, and `assumptions` sections of a DesignPackage. Preserve unknowns in `open_decisions`.

## Safety and public boundary / 安全与公开边界

- Keep physical output disabled by default and do not generate executable hardware commands.
- Specify hardware functions and interfaces, never vendor, model, part number, serial number, account, endpoint, or credential.
- Treat the output as an engineering design proposal, not a safety certification.

## Completion / 完成条件

Return the filled template and run the DesignPackage validator after downstream sections are complete.
