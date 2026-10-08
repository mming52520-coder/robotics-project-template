# ADR-0003: Add a simulation-only ROS 2 execution slice

- Status: accepted
- Date: 2026-10-08
- Owners: repository maintainers

## Context

The v0.2 repository validates design documents but contains no executable ROS 2 graph. A user needs a runnable, reviewable engineering starting point. The verified synthetic `warehouse-tote` design calls for one safety gate before a base interface, bounded velocity requests, command expiry, and fault-injection evidence.

The public [ros2-engineering-skills](https://github.com/dbwls99706/ros2-engineering-skills) project was reviewed on 2026-10-08. Its README, `docs/QUALITY_GATES.md`, `docs/ROS_CI.md`, and `references/testing.md` distinguish static checks from observed ROS behavior and require explicit evidence boundaries. Its license is Apache-2.0. These are workflow references; no source code or configuration is copied.

## Decision

Keep the existing model-free DesignBrief and DesignPackage workflow. Add one ROS 2 Jazzy `ament_python` package under `src/` with a pure Python safety core, a ROS safety-gate adapter, a fake kinematic base, synthetic status inputs, a launch file, and a ROS graph regression. Every executable path remains simulation-only. Run offline checks and a separate ROS build/test gate in CI.

## Rejected alternatives

- Add a hardware driver: no verified device contract, measured stop behavior, or authorization exists.
- Add Nav2 and a full robot model now: map, frames, sensors, and dynamics are still open decisions in the synthetic design.
- Treat a successful static validator as runtime evidence: it cannot prove that nodes communicate or time out correctly.

## Verification and limits

Validate the synthetic design pair, run offline unit tests, build with Jazzy, run the ROS pytest suite and inspect `colcon test-result`, then smoke-test the installed launch. These prove only the specified simulation behavior. Before physical work, a project-specific design and human-reviewed safe test procedure remain required.
