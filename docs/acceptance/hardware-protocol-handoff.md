# Hardware and protocol handoff acceptance

- Candidate: `codex/hardware-protocol-handoff`, based on local `4654718`.
- Scope: Agent rules, private selection/protocol workflow, Git-aware public checks,
  one future Agent behavior case, the installed-launch reset readiness test, and
  documentation. No robot runtime changed.
- Baseline: public DesignPackage v2 was model-free; the fake ROS base had no real
  device adapter; public validators rejected any locally ignored private file.

| Item | Result | Evidence or limit |
|---|---|---|
| Public DesignPackage remains model-free | PASS | No Schema or synthetic example changed; design validators pass. |
| Requirement to private selection and protocol-pending algorithm | PASS (rule) | `AGENTS.md`, hardware/navigation Skills, and handoff reference define outputs, trace IDs, sources, unknowns, and fake/replay interface work. No real project requirement was supplied. |
| Protocol receipt to adapter | PASS (rule) | Handoff reference requires version, framing, units, timing, error, stop, and fake-transport checks. No protocol or adapter was supplied or implemented. |
| Local private data is ignored; force-tracked private data is rejected | PASS | Unit regression creates an ignored candidate, force-adds it, and checks both public scanner and template errors. |
| Installed-launch startup readiness | PASS | The test now waits boundedly for healthy synthetic status and observed fake-base odometry. It still checks zero output before reset and motion only after reset; the final targeted test passed three times locally. |
| Offline project checks | PASS | `bash scripts/run-checks.sh`: 54 unit tests, contract/Skill/eval/public checks, Ruff, YAML, Markdown, and ShellCheck. |
| Jazzy simulation checks | PASS | `bash scripts/run-ros-checks.sh`: build, 4 ROS tests, design/JUnit trace, 0 errors/failures/skips. |
| Real product selection and purchase | BLOCKED | No project-specific physical requirements, current candidate evidence, or engineer purchase decision. |
| Real protocol integration | BLOCKED | No received hardware, protocol revision, or recorded frames. |
| Physical trial | BLOCKED | No hardware/site evidence or responsible-human approval of a safe procedure. Physical output remained disabled. |
| Separate Agent workflow evaluation | NOT RUN | `evals/workflow-cases/05-protocol-is-not-trial-approval.json` is a future case definition only. |
| Independent review and remote CI | NOT RUN | Candidate needs a separate reviewer and fresh CI before merge consideration. |

The first offline run failed the inherited ChangeContract because the private notice
was outside its allowed paths; the contract was updated. The second run exposed Ruff
format errors, and the third exposed a YAML line-length error. Both were corrected.
An initial ROS run used the offline virtual environment, which lacked `pytest`;
the system Jazzy Python run completed successfully. Failed runs remain in ignored
`artifacts/` alongside the passing manifests and raw logs.
One later full Jazzy run intermittently rejected reset while the synthetic status
publishers were starting. The next full run reached a motion command before the fake
base's first odometry observation. Both fixed waits raced ROS discovery; the test now
waits within a deadline for the existing gate conditions and actual fake-base output.
Gate logic and thresholds were not changed. Both failure manifests are retained;
the final targeted restart test passed three consecutive runs after the change.

Review the candidate diff against `4654718`, inspect the test assertion and Git
ignore behavior, rerun both check scripts on the final snapshot, and validate their
manifests before merge. Do not merge this branch solely on this self-review.
