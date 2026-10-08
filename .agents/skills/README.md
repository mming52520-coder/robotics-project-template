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

For a bounded code change based on an existing validated design, use
`robotics-change-plan` to state scope, `robotics-bounded-implementation` to change
only that scope and run checks, then `robotics-evidence-review` for a read-only
review of the diff and evidence. These three Skills do not replace the five design
Skills when the design itself changes. None of their files can record human approval.

An AGENTS.md-aware coding Agent should run that sequence within one user request:
the user describes a feature or bug, and the Agent writes the actual code and tests,
reviews the result, fixes confirmed findings, and returns the final diff and evidence.
The plan-stage ChangeContract may reference planned test IDs; the final gate requires
implemented tests. Separate human approval is only needed for unresolved safety,
hardware, or scope decisions, and before any unrequested remote action.

For hardware-dependent requirements, `mobile-robot-hardware-planning` keeps the public
DesignPackage model-free and may create an ignored private selection list for engineer
purchase review. Navigation and implementation work may use fake/replay interfaces
while device protocols are pending. Follow
`docs/reference/hardware-protocol-handoff.md` when the engineer later supplies
protocols; only a separate safe procedure can authorize a physical trial.
