# Design contracts / 设计契约

`DesignBrief v1` is the user-supplied input. `DesignPackage v2` is the AI-assisted, reviewable output.

## v2 upgrade

The package schema and validator now require `schema_version: "v2"`. Existing v1 packages
must be upgraded explicitly; a v1 file is not silently treated as complete. The three synthetic
examples have been upgraded. Keep the v1 DesignBrief and its `brief_id`.

For each package, add stable `requirements` IDs with DesignBrief JSON-pointer `source` values.
Give every interface, algorithm, hardware function, and safety plan an ID and
`requirement_ids`. Interfaces require an owner, producer, consumer, data meaning, units,
frame, freshness, and failure behavior. Safety limits and timeouts must be finite positive
numbers; the linear limit cannot exceed the brief's maximum speed. Add structured
`verification_plan.checks` with scenario, acceptance, evidence, and status.

An implemented requirement also needs one `traceability` row. Its design IDs and
implemented test IDs must exactly match the reverse links in the package. File and Python
symbol references, test nodes, and ROS interface names are checked. Planned requirements
keep a design link and a planned verification check without claiming executable evidence.
Unknown safety gates or speed limits block package validation even when the brief records
a blocker. Validation establishes contract completeness; it does not certify robot safety.

## Workflow / 工作流

1. Start from a synthetic example in `examples/` and replace only verified project facts.
2. Validate the brief before asking an AI to design the robot.
3. Invoke the five Skills in the documented order.
4. Validate the completed package before review.

```text
python tools/validate_design_package.py BRIEF.json
python tools/validate_design_package.py BRIEF.json PACKAGE.json
```

After running the Jazzy ROS tests, check the generated JUnit evidence with:

```text
python3 tools/validate_design_package.py BRIEF.json PACKAGE.json --evidence build/robotics_sim/test_results/robotics_sim/pytest.xml
```

Use JSON as the canonical machine-readable form. Use companion Markdown only to explain context for people. Do not place product identities, credentials, customer data, endpoints, or real site information in either artifact.
