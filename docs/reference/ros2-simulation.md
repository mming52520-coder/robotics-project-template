# ROS 2 simulation contract / ROS 2 仿真契约

## Scope and source

This is a synthetic, simulation-only slice of `examples/warehouse-tote/`. Its DesignBrief and DesignPackage pass `tools/validate_design_package.py`. ROS 2 Jazzy is the tested target. The package does not implement localization, planning, obstacle detection, hardware actuation, or a safety-rated emergency stop.

## Graph

| Interface | Type | Producer | Consumer | Rule |
| --- | --- | --- | --- | --- |
| `/sim/cmd_request` | `geometry_msgs/Twist` | test/operator | safety gate | linear x in ±0.6 m/s, angular z in ±1.0 rad/s; other axes zero |
| `/sim/emergency_stop` | `std_msgs/Bool` | synthetic environment | safety gate | true latches stop until explicit reset |
| `/sim/health_ok` | `std_msgs/Bool` | synthetic environment | safety gate | false stops and discards command |
| `/sim/obstacle_clear` | `std_msgs/Bool` | synthetic environment | safety gate | false stops and discards command |
| `/sim/cmd_safe` | `geometry_msgs/Twist` | safety gate | fake base | zero unless all inputs are fresh and safe |
| `/sim/odom` | `nav_msgs/Odometry` | fake base | observer | `odom` to `base_link`, synthetic kinematics |
| `/sim/reset_estop` | `std_srvs/Trigger` | operator | safety gate | succeeds only with fresh, clear inputs; discards old command |

The gate publishes at 20 Hz and starts with its emergency-stop latch set. It accepts motion only after fresh, clear status inputs and an explicit `/sim/reset_estop` call; a recreated gate requires the same reset. A request expires after 0.25 s; each status expires after 0.3 s. The fake base independently expires safe commands after 0.2 s. All freshness checks use monotonic process time. A missing input, fault, invalid request, or timeout produces zero velocity. The gate does not treat receipt of a zero Twist as proof of a physical stop. If the gate process exits while motion is active, the fake base may continue the last safe command for up to its 0.2 s timeout; the test observes eventual zero synthetic odometry but does not measure exact stopping latency.

The synthetic environment sends the three status topics at 10 Hz. Its `emergency_stop`, `health_ok`, and `obstacle_clear` parameters can be changed while running for fault injection. It is deliberately not a device interface. The package has no output path to an actuator.

## Verification and limits

| Gate | Evidence | Limit |
| --- | --- | --- |
| Design contract | `tools/validate_design_package.py` on the synthetic v1 brief and v2 package | Completeness and static trace links |
| Offline unit | `tests/unit/test_sim_core.py` | Motion and timeout logic only |
| ROS graph | `python3 -m pytest -q src/robotics_sim/test/test_*.py --junitxml=build/robotics_sim/test_results/robotics_sim/pytest.xml` after build | Pub/sub, services, in-process gate recreation, separate process restart, and installed node startup |
| Evidence link | `tools/validate_design_package.py BRIEF PACKAGE --evidence build/robotics_sim/test_results/robotics_sim/pytest.xml` | Every implemented check ID resolves to a passing JUnit case |
| Launch smoke | `ros2 launch robotics_sim sim.launch.py` and topic observation | Manual startup and installed parameter inspection in Jazzy |

The ROS graph test covers motion bounds, health and obstacle faults, emergency-stop latch, reset, command expiry, and in-process gate recreation. The installed tests check three separate node processes start at zero, observe fake-base command expiry after the gate exits, and restart a safety-gate process after synthetic motion. These four tests and their JUnit evidence passed locally in Jazzy on the PR #18 acceptance worktree; candidate GitHub CI has not run. No field performance or physical safety claim follows from these checks. Before any real robot project uses this pattern, identify actual sensors, braking and stopping requirements, independent stop paths, timing budgets, diagnostics, measured evidence, and a supervised trial procedure in a project-specific DesignPackage.
