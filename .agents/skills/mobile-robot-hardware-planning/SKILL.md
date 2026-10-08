---
name: mobile-robot-hardware-planning
description: Produce a model-free public hardware plan and, when a project requirement supports it, a separate private hardware selection list for engineer review. Use for sensing, compute, power, feedback, communication, installation, and safe degradation before procurement.
---

# Mobile Robot Hardware Planning / 移动机器人硬件规划

Read `references/model-free-policy.md` and `assets/hardware-function-template.md`. Use the DesignBrief, algorithm prerequisites, and safety plan as inputs.

## Workflow / 工作流

1. Translate each required capability into a functional block: motion feedback, obstacle observation, compute, power, communication, diagnostics, and mechanical installation.
2. State measurable performance requirements, interface properties, environmental constraints, health reporting, and safe degradation for each block.
3. Trace every hardware block to an algorithm prerequisite or safety requirement. Mark untraceable blocks as optional rather than required.
4. Keep the public DesignPackage at capability level. Replace a supplied product name
   or part number there with the capability and acceptance requirement it represents.
5. Write the `hardware_functional_plan` section of the DesignPackage and add procurement-dependent items to `open_decisions`.
6. When the project needs hardware and its requirements support concrete selection,
   follow `docs/reference/hardware-protocol-handoff.md`. Create the selection list only
   under ignored `config/private/`; link each candidate to a requirement and functional
   hardware ID, dated manufacturer evidence, fit gaps, protocol availability, and an
   engineer's pending purchase decision. Mark unsupported candidates open, not selected.

## Safety and public boundary / 安全与公开边界

- Never put vendor, manufacturer, model, part number, serial number, device identity, customer site, network endpoint, account, or credential in public output. A private selection list may name candidate products but must not contain credentials or private network endpoints.
- Do not purchase hardware or claim an engineer approved a candidate.
- Do not specify unverified electrical ratings as facts; mark them open until measured or approved by the responsible engineer.
- Require a physical safety review before any hardware output is enabled.

## Completion / 完成条件

Every hardware entry must contain function, performance requirements, interface, environment, and degradation behavior.
