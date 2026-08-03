# Robotics Project Template

A public, model-free template for AI-assisted design of controlled indoor wheeled robots. It helps an AI turn a structured requirement into a reviewable ROS 2 reference architecture, algorithm plan, hardware functional plan, safety plan, and verification plan.

这是一个公开、型号无关的模板，用于 AI 辅助设计受控环境中的室内轮式机器人。它将结构化需求转为可审查的 ROS 2 参考架构、算法方案、硬件功能方案、安全方案和验证计划。

The repository does not include product code, hardware drivers, product recommendations, real configuration, or permission to actuate physical hardware. Examples are synthetic and physical output is disabled by default.

Before starting a new architecture, use `open-source-architecture-research` to inspect the current
project and compare high-signal public references. The Skill records reproducible evidence; the AI
then derives a separately reviewable architecture recommendation from that evidence. It does not
clone code or choose products.

## Quick start / 快速开始

1. Select **Use this template** on GitHub.
2. Copy a synthetic DesignBrief from `examples/` and replace it with verified project facts only.
3. Validate the brief, invoke the Skills in sequence, and validate the final package.

```text
python tools/validate_design_package.py examples/warehouse-tote/design-brief.json
python tools/validate_design_package.py examples/warehouse-tote/design-brief.json examples/warehouse-tote/design-package.json
```

1. Review `contracts/README.md`, `docs/reference/`, and the documented safety gate before any implementation work.

## Structure

```text
.
├── .agents/skills/        # Five design Skills plus architecture research
├── contracts/             # Versioned DesignBrief and DesignPackage schemas
├── evals/                 # Positive and safety-blocking Skill cases
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
├── src/
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
6. Update architecture decisions and working memory / 更新架构决策与工作记忆。

## Model-free policy / 型号无关政策

- Describe hardware functions, interfaces, performance, health signals, environment, and degradation behavior.
- Never commit or generate vendor, model, part number, serial number, customer data, site data, endpoint, account, or credential.
- Treat a user-provided product identity as a capability constraint; do not copy it into a public artifact.

## Safety boundary / 安全边界

- Default hardware-related work to simulation, fake transports, or offline replay.
- Do not weaken stop, interlock, watchdog, limit, or fault-recovery behavior.
- Do not commit credentials, customer or personal data, device identities, site maps, private endpoints, or production parameters.
- Do not treat this template as safety certification, procurement advice, or permission to actuate physical equipment.

## Validate / 校验

```text
python tools/validate_template.py
python tools/validate_skills.py
python tools/validate_evals.py
python tools/validate_public_content.py
python -m unittest discover -s tests/unit -p "test_*.py"
python -m ruff check tools
yamllint --config-file .yamllint.yaml .
pymarkdown --config .pymarkdown.json scan .
shellcheck scripts/*.sh
```

## License / 许可证

Licensed under Apache License 2.0.
