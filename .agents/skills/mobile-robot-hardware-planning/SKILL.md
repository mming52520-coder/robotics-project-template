---
name: mobile-robot-hardware-planning
description: Produce a vendor-neutral functional hardware plan for a controlled indoor wheeled robot, including sensing, compute, power, motion feedback, communication, installation, and degradation requirements. Use when a DesignBrief needs a safe hardware architecture without recommending concrete products or procurement choices.
---

# Mobile Robot Hardware Planning / 移动机器人硬件规划

Read `references/model-free-policy.md` and `assets/hardware-function-template.md`. Use the DesignBrief, algorithm prerequisites, and safety plan as inputs.

## Workflow / 工作流

1. Translate each required capability into a functional block: motion feedback, obstacle observation, compute, power, communication, diagnostics, and mechanical installation.
2. State measurable performance requirements, interface properties, environmental constraints, health reporting, and safe degradation for each block.
3. Trace every hardware block to an algorithm prerequisite or safety requirement. Mark untraceable blocks as optional rather than required.
4. Keep selection at capability level. Replace any supplied product name or part number with the capability and acceptance requirement it represents.
5. Write the `hardware_functional_plan` section of the DesignPackage and add procurement-dependent items to `open_decisions`.

## Safety and public boundary / 安全与公开边界

- Never output vendor, manufacturer, model, part number, serial number, device identity, customer site, network endpoint, account, or credential.
- Do not specify unverified electrical ratings as facts; mark them open until measured or approved by the responsible engineer.
- Require a physical safety review before any hardware output is enabled.

## Completion / 完成条件

Every hardware entry must contain function, performance requirements, interface, environment, and degradation behavior.
