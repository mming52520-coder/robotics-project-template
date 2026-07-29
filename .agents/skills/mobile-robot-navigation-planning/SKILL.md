---
name: mobile-robot-navigation-planning
description: Plan localization, mapping, global routing, local collision-aware tracking, recovery, and their failure behavior for a controlled indoor wheeled robot. Use when an AI needs to add or review a mobile-robot algorithm plan from a DesignBrief without selecting hardware products or commanding a physical robot.
---

# Mobile Robot Navigation Planning / 移动机器人导航规划

Read `references/navigation-choice-matrix.md` and `assets/algorithm-plan-template.md`. Use a validated DesignBrief and system design as inputs.

## Workflow / 工作流

1. Identify the required capability, kinematics, environment change rate, operating envelope, and safety constraints.
2. Choose a state-estimation approach, map representation, global route planner, local collision-aware tracker, and recovery behavior. State why each choice fits the evidence.
3. List prerequisites: calibrated frames, time synchronization, observation freshness, route limits, and replay data.
4. Define measurable failure behavior for localization loss, stale observations, blocked route, and planner failure. Default to degraded operation or zero motion.
5. Add model-free sensor capabilities only when they are necessary to support an algorithm prerequisite; defer unverified capability to `open_decisions`.
6. Write the `algorithm_plan` section of the DesignPackage.

## Safety and public boundary / 安全与公开边界

- Do not claim collision avoidance is a safety guarantee.
- Do not select or name hardware products, calibration values, map files, sites, or real recordings.
- Do not create a path that bypasses the safety gate.

## Completion / 完成条件

Use the template and provide one simulation or replay scenario for every algorithm failure mode.
