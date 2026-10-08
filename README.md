# Robotics Project Template

本项目用于 AI 辅助设计轮式机器人。它将结构化需求转为可审查的 ROS 2 架构、算法方案、硬件功能方案、安全方案和测试计划。
实现工作以经过校验的设计包和受限变更合同为依据；测试执行结果须有原始证据。
The repository includes a simulation-only ROS 2 package. It has no hardware drivers, published product recommendations, real configuration, or permission to actuate physical hardware. Examples are synthetic and physical output is disabled by default.

Before starting a new architecture, use `open-source-architecture-research` to inspect the current
project and compare high-signal public references. The Skill records reproducible evidence; the AI
then derives a separately reviewable architecture recommendation from that evidence. It does not
clone code or choose products.

## Quick start / 快速开始

1. Clone this repository. The upstream repository's GitHub template setting was not enabled
   when last checked; use **Use this template** only after the owner enables it.
2. Open the checkout with an AGENTS.md-aware coding Agent and describe the behavior you want.
   The Agent should inspect the repository, then create or update the relevant design and
   ChangeContract, write code and tests, review the diff, fix confirmed findings, and
   return the final evidence in the same task.
3. For a new robot design, copy a synthetic DesignBrief and replace it with verified
   project facts. The Agent then runs the relevant design Skills before implementation.
4. Review `contracts/README.md`, `docs/reference/`, and the safety gate before physical work.

For a new robot capability, the Agent can make a private, source-backed hardware
selection list and implement protocol-pending algorithms against fake/replay interfaces.
When an engineer later supplies the purchased device's protocol, the Agent can build
and review an adapter with offline evidence. A supervised vehicle trial remains a
separate authorized stage. See [hardware and protocol handoff](docs/reference/hardware-protocol-handoff.md).

For example, a user can say: “Add a read-only timeout diagnostic to the simulated base.
Keep motion gating unchanged. Implement it, test it, review the code, and report the
evidence.” The Agent derives the detailed acceptance and code scope from the repository;
the prompt is a request for implementation, not merely a test run. The exact workflow
and stop conditions are in [Agent development workflow](docs/reference/agent-development-workflow.md).

```text
python tools/validate_design_package.py examples/warehouse-tote/design-brief.json
python tools/validate_design_package.py examples/warehouse-tote/design-brief.json examples/warehouse-tote/design-package.json
```

## Run the ROS 2 simulation / 运行 ROS 2 仿真

The `robotics_sim` package implements the synthetic `warehouse-tote` package's motion interface with a safety gate, fake base, and switchable simulated safety inputs. It does not launch navigation or connect to a device. Use ROS 2 Jazzy on Ubuntu 24.04; from the repository root:

```bash
source /opt/ros/jazzy/setup.bash
colcon build --packages-select robotics_sim
source install/setup.bash
ros2 launch robotics_sim sim.launch.py
```

In another sourced terminal, inspect the zero-motion default, then publish a bounded synthetic request:

```bash
ros2 topic echo /sim/cmd_safe
ros2 service call /sim/reset_estop std_srvs/srv/Trigger '{}'
ros2 topic pub -r 10 /sim/cmd_request geometry_msgs/msg/Twist \
  '{linear: {x: 0.2}, angular: {z: 0.0}}'
ros2 topic echo /sim/odom
```

The gate starts latched, so the reset succeeds only after the synthetic status inputs are fresh and clear. Stop the request publisher; its 0.25-second timeout makes the next gate publication zero. To inject a fault, run `ros2 param set /sim/sim_environment emergency_stop true`. Clear it with `ros2 param set /sim/sim_environment emergency_stop false`, then call `ros2 service call /sim/reset_estop std_srvs/srv/Trigger '{}'` and publish a fresh request. A restarted gate also requires reset. The same parameter interface exposes `health_ok` and `obstacle_clear`. See [simulation contract](docs/reference/ros2-simulation.md) for exact topic, timeout, fault, and evidence boundaries.

Run `bash scripts/run-checks.sh` for the repository checks and, on a host with ROS 2 Jazzy,
`bash scripts/run-ros-checks.sh` for the simulation build, graph tests, JUnit trace check,
and test-result inspection. Both scripts write raw logs and a bound manifest under the
ignored `artifacts/<run-id>/` directory. CI uses the same scripts and uploads their
available results, including JUnit. See [contracts](contracts/README.md) for evidence limits.

## Structure

```text
.
├── .agents/skills/        # Design, bounded implementation, and review Skills
├── changes/               # Bounded ChangeContracts for candidate changes
├── contracts/             # Versioned design and change schemas
├── evals/                 # Contract fixtures and unrun workflow case definitions
├── examples/              # Synthetic validated design packages
├── config/
│   ├── example/           # Safe, shareable defaults
│   └── private/           # Ignored local or production values
├── docs/
│   ├── architecture/
│   ├── decisions/
│   └── work-memory/
├── experiments/
├── research/               # Ignored local architecture-research artifacts
├── scripts/
├── src/robotics_sim/      # ROS 2 Jazzy simulation-only package
└── tests/
    ├── unit/
    ├── integration/
    └── replay/
```

## Operating model / 运行模式

1. When selecting a reference architecture, research public high-signal projects and record sources / 选择参考架构时先调研公开高质量项目并记录来源。
2. Fill and validate a DesignBrief / 填写并校验 DesignBrief。
3. Run system design, navigation, hardware, safety, and verification Skills / 按顺序运行五个 Skill。
4. Validate the DesignPackage and keep uncertainties as blockers or open decisions / 校验设计包，保留不确定性。
5. Implement only after simulation, fake transport, or replay evidence is planned / 先规划仿真、虚拟传输或回放证据。
6. Write a ChangeContract, generate code and tests, run shared checks, review the exact diff,
   fix confirmed findings, and recheck the final snapshot / 为单次变更完成代码、测试和复核。
7. Update architecture decisions and working memory / 更新架构决策与工作记忆。
8. For a project requiring hardware, prepare a private selection list, then integrate
   received protocols with fake/replay evidence before a separately approved physical
   trial / 项目需要硬件时，先形成私有选型清单，收到协议后完成离线适配验证，再单独审批实车试验。

## Model-free policy

- Describe hardware functions, interfaces, performance, health signals, environment, and degradation behavior.
- Never put vendor, model, part number, serial number, customer data, site data,
  endpoint, account, or credential in a public artifact. Concrete candidate identities
  may be kept in ignored local `config/private/` for engineer review.
- Treat a user-provided product identity as a capability constraint in the public
  DesignPackage; keep its identity and protocol document private.

## Safety boundary

- Default hardware-related work to simulation, fake transports, or offline replay.
- Do not weaken stop, interlock, watchdog, limit, or fault-recovery behavior.
- Do not commit credentials, customer or personal data, device identities, site maps, private endpoints, or production parameters.
- Do not treat this template as safety certification, procurement advice, or permission to actuate physical equipment.

## Validate / 校验

```bash
python3 -m pip install --requirement requirements-dev.txt
bash scripts/run-checks.sh
bash scripts/run-ros-checks.sh  # ROS 2 Jazzy host or CI container only
```

The last command runs simulated ROS nodes only. OCR review is optional and read-only;
it is never a substitute for the deterministic checks or human acceptance. See
[delivery gates](docs/reference/github-delivery-gates.md) before changing GitHub settings.

## License / 许可证

Licensed under Apache License 2.0.
