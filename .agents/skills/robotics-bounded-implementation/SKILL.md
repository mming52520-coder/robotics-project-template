---
name: robotics-bounded-implementation
description: Implement one approved robotics ChangeContract in an isolated branch and produce deterministic test evidence. Use for source changes after the change scope is settled.
---

# Robotics Bounded Implementation

Read the current ChangeContract and `references/scope-and-evidence.md`. Start from its
base revision in an isolated worktree. Keep the existing design and ROS safety behavior
unless the authorized change explicitly revises them.

1. Trace affected implementation paths and reuse existing helpers before editing.
2. Make the smallest correct change inside the declared paths. Stop if a new requirement,
   interface meaning, safety threshold, or file outside scope becomes necessary.
3. Run `scripts/run-checks.sh` and, for ROS behavior or evidence links,
   `scripts/run-ros-checks.sh`. Keep the generated manifest, raw logs, and JUnit results.
4. Hand the diff and evidence to a separate read-only review. Record unmet gates as
   blocked or failed; never self-report an unrun check as passed.

## Safety and public boundary

- Do not enable actuator output or touch physical hardware.
- Do not weaken safety gates, test assertions, or evidence checks to obtain a pass.
- Commit, push, merge, and remote setting changes require their own user authorization.
- Keep secrets, real device identifiers, and private operational facts out of the repository.
