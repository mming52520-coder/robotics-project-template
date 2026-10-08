---
name: robotics-bounded-implementation
description: Generate code and regression tests for a user-authorized robotics change in an isolated branch, then produce deterministic evidence and hand it to read-only review.
---

# Robotics Bounded Implementation

Read the current ChangeContract, user request, and `references/scope-and-evidence.md`.
Work in an isolated task branch or worktree. The validated plan bounds the edit but
does not replace the user's authorization. Preserve ROS safety behavior unless the
requested change explicitly revises it and its safety basis is resolved.

1. Trace affected implementation paths and reuse existing helpers before editing.
2. Make the smallest correct change inside the declared paths. Stop if a new requirement,
   interface meaning, safety threshold, or file outside scope becomes necessary.
3. Update planned design links to the actual implementation and test nodes. Run
   `python3 tools/validate_change_contract.py --phase final`, then
   `scripts/run-checks.sh` and, for ROS behavior or evidence links,
   `scripts/run-ros-checks.sh`. Keep the generated manifest, raw logs, and JUnit results.
4. Continue to `robotics-evidence-review` in the same user task. Return confirmed
   findings to implementation, make bounded fixes, and regenerate evidence for the
   final snapshot. Record unmet gates as blocked or failed; never call an unrun check pass.

## Safety and public boundary

- Do not enable actuator output or touch physical hardware.
- Do not weaken safety gates, test assertions, or evidence checks to obtain a pass.
- Commit, push, merge, and remote setting changes require their own user authorization.
- Keep secrets, real device identifiers, and private operational facts out of the repository.
