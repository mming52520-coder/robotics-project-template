# Design contracts / 设计契约

`DesignBrief` is the user-supplied input. `DesignPackage` is the AI-assisted, reviewable output.

## Workflow / 工作流

1. Start from a synthetic example in `examples/` and replace only verified project facts.
2. Validate the brief before asking an AI to design the robot.
3. Invoke the five Skills in the documented order.
4. Validate the completed package before review.

```text
python tools/validate_design_package.py BRIEF.json
python tools/validate_design_package.py BRIEF.json PACKAGE.json
```

Use JSON as the canonical machine-readable form. Use companion Markdown only to explain context for people. Do not place product identities, credentials, customer data, endpoints, or real site information in either artifact.
