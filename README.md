# Robotics Project Template

A public, hardware-safe starting point for robotics and embedded projects that need traceable architecture, experiments, verification, and AI-assisted handoffs.

The repository contains process scaffolding rather than product code. Example configuration is synthetic and physical hardware output is disabled by default.

## Use this template

1. Select **Use this template** on GitHub.
2. Replace placeholder text in `docs/architecture/` and `docs/work-memory/current.md`.
3. Put shareable defaults in `config/example/`.
4. Keep local and production values in `config/private/`; its contents are ignored.
5. Define project-specific checks in `scripts/run-checks.sh`.
6. Record material experiments and architectural decisions.

## Structure

```text
.
├── .agents/skills/        # Project-local Agent Skills
├── config/
│   ├── example/           # Safe, shareable defaults
│   └── private/           # Ignored local or production values
├── docs/
│   ├── architecture/
│   ├── decisions/
│   └── work-memory/
├── experiments/
├── scripts/
├── src/
└── tests/
    ├── unit/
    ├── integration/
    └── replay/
```

## Operating model

1. Define the objective and acceptance criteria.
2. Record architecture and interface contracts.
3. Implement the smallest safe change.
4. Verify with unit, integration, simulation, or replay evidence.
5. Record decisions, experiment results, and unresolved risks.
6. Update working memory so a fresh contributor can continue without guessing.

## Safety boundary

- Default hardware-related work to simulation, fake transports, or offline replay.
- Do not weaken stop, interlock, watchdog, limit, or fault-recovery behavior.
- Do not commit credentials, customer or personal data, device identities, site maps, private endpoints, or production parameters.
- Do not treat this template as safety certification or permission to actuate physical equipment.

## Validate

```text
python tools/validate_template.py
python -m ruff check tools
yamllint --config-file .yamllint.yaml .
pymarkdown --config .pymarkdown.json scan .
shellcheck scripts/*.sh
```

## License

Licensed under Apache License 2.0.
