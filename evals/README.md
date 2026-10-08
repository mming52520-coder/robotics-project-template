# Evaluation groups

`cases/` contains the original three positive and three negative fixed design fixtures.
`workflow-cases/` defines failure scenarios for future real Agent behavior evaluations. The
fixture validator checks that these declarations are well formed; it does not run an Agent.
Every workflow case remains `agent_run_status: not_run` until a separate, versioned Agent
experiment records model, Skill version, input, tool actions, and outcome outside this suite.

Deterministic negative coverage for contract scope and stale execution evidence belongs in
`tests/unit/`. Do not count those unit tests as observed Agent behavior.
