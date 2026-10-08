# Design contracts / 设计契约

`DesignBrief v1` is the user-supplied input. `DesignPackage v2` is the AI-assisted,
reviewable output. The CLI needs Python `jsonschema` for Draft 2020-12 validation;
`requirements-dev.txt` pins the checked version. ROS runtime nodes do not import it.

## v2 upgrade

The package schema and validator now require `schema_version: "v2"`. Existing v1 packages
must be upgraded explicitly for implementation or evidence claims. The archived
`design-package.v1.schema.json` remains available through `--legacy-design-only`,
which validates a v1 file as a design artifact and rejects `--evidence`. The three
synthetic examples have been upgraded. Keep the v1 DesignBrief and its `brief_id`.

For each package, add stable `requirements` IDs with DesignBrief JSON-pointer `source` values.
Give every interface, algorithm, hardware function, and safety plan an ID and
`requirement_ids`. Interfaces require an owner, producer, consumer, data meaning, units,
frame, freshness, and failure behavior. Safety limits and timeouts must be finite positive
numbers; the linear limit cannot exceed the brief's maximum speed. Add structured
`verification_plan.checks` with preconditions, scenario, acceptance, evidence, and status.
Each requirement has a scope and measurable acceptance statement. Open decisions name
affected requirements, whether they block implementation, and the evidence needed to close them.

An implemented requirement also needs one `traceability` row. Its design IDs and
implemented test IDs must exactly match the reverse links in the package. File and Python
symbol references, test nodes, and ROS interface names are checked. Planned requirements
keep a design link and a planned verification check without claiming executable evidence.
Unknown safety gates or speed limits block package validation even when the brief records
a blocker. Validation establishes contract completeness; it does not certify robot safety.

## Workflow / 工作流

1. Start from a synthetic example in `examples/` and replace only verified project facts.
2. Validate the brief before asking an AI to design the robot.
3. Invoke the five design Skills in the documented order when creating or revising a design.
4. Validate the completed package, then declare the specific repository change in a
   `changes/<change-id>/change.json` ChangeContract before implementation.

```text
python tools/validate_design_package.py BRIEF.json
python tools/validate_design_package.py BRIEF.json PACKAGE.json
python tools/validate_design_package.py BRIEF.json OLD-V1-PACKAGE.json --legacy-design-only
python tools/validate_change_contract.py changes/<change-id>/change.json
```

After running the Jazzy ROS tests, check the generated JUnit evidence with:

```text
python3 tools/validate_design_package.py BRIEF.json PACKAGE.json --evidence build/robotics_sim/test_results/robotics_sim/pytest.xml
```

Use JSON as the canonical machine-readable form. Use companion Markdown only to explain context for people. Do not place product identities, credentials, customer data, endpoints, or real site information in either artifact.

The ChangeContract binds a specific diff to a DesignPackage digest, requirement IDs, paths,
invariants, and required executable test IDs. Its validation does not prove human approval.
Generated evidence under `artifacts/` records the actual checked-out SHA, candidate PR head,
raw logs, JUnit results, and per-test trace results. A complete link is an audit trail, not
proof that the assertion has the intended meaning; reviewers must inspect that meaning.
