# Project-local Skills / 项目级 Skill

The repository ships an ordered, model-free indoor mobile-robot design workflow:

0. `open-source-architecture-research` (optional evidence-gathering step before a local design)

1. `mobile-robot-system-design`
2. `mobile-robot-navigation-planning`
3. `mobile-robot-hardware-planning`
4. `mobile-robot-control-safety`
5. `mobile-robot-verification-plan`

Start only from a validated `DesignBrief`; complete a `DesignPackage` before implementation or physical testing.
When external architecture references are needed, run the research Skill first and keep its generated
research artifacts local and ignored until a human has reviewed their sources and license boundary.

Additional focused project-level Agent Skills use this layout:

```text
.agents/skills/example-skill/
├── SKILL.md
├── agents/openai.yaml
├── references/
├── scripts/
└── assets/
```

Every Skill must have a valid `SKILL.md`, a single clear responsibility, explicit safety boundaries, and evaluation cases appropriate to its behavior. Public Skills and examples must remain free of hardware identities, private data, and credentials.
