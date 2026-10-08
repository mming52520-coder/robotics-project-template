# Requirement-to-code Agent workflow acceptance

- Date: 2026-10-08
- Branch: `codex/agent-requirement-delivery`, based on local `1a1a2f2`
- Scope: repository guidance and the ChangeContract plan/final transition
- ROS control code: unchanged; physical output: disabled

## Expected user experience

A user opens this checkout in an AGENTS.md-aware coding Agent and enters a feature or
defect request. `AGENTS.md` now routes that one request through design as needed,
ChangeContract planning, actual source and test edits, deterministic checks, read-only
diff review, bounded fixes, and a final handoff. The Agent must identify self-review
honestly and ask for a concrete decision when safety or hardware authority is unknown.
The user does not need to invoke each Skill manually for an ordinary local change.

## Verified gates

| Gate | Result | Evidence |
| --- | --- | --- |
| Planned requirement can enter implementation | PASS | A real planned warehouse-tote requirement and planned test pass `--phase plan`. |
| Planned-only result cannot pass final gate | PASS | The same pair fails `--phase final`; a mismatched test link fails planning. |
| Existing implemented contracts | PASS | Current ChangeContract passes both phases and shared final runner. |
| Offline repository checks | PASS | 53 unit tests, design and content checks, Skills, Ruff, YAML, Markdown, ShellCheck. |
| Jazzy simulation regression | PASS | Four ROS tests, installed launch, JUnit trace, and `colcon test-result` passed locally. |
| Self-review of this change | PASS | Incremental diff, caller paths, existing planned links, and test assertions inspected; no actionable finding confirmed. |
| Independent review of changed validator/instructions | BLOCKED | The implementing Agent's self-review is not an independent human review. |
| Separate Agent behavior evaluation | NOT RUN | The positive workflow case is a definition; no isolated Agent run produced code/review artifacts. |
| Fresh GitHub CI and merge | NOT RUN | This branch remains local and has not been pushed or merged. |

## Commands and artifacts

```bash
python3 tools/validate_change_contract.py changes/ai-delivery-chain/change.json --phase plan
python3 tools/validate_change_contract.py changes/ai-delivery-chain/change.json --phase final
bash scripts/run-checks.sh
bash scripts/run-ros-checks.sh
python3 tools/evidence.py validate artifacts/<run-id>
git diff --check
```

The check scripts retain exact commands and raw logs in ignored `artifacts/<run-id>/`.
The ROS manifest links DesignPackage test IDs to passing JUnit cases and the tested
workspace snapshot. A self-review record is also kept under ignored `artifacts/` so it
does not change the checked source snapshot.

## Remaining acceptance

Before treating this as a reusable feature for people cloning the public repository,
review the final merged diff against a trusted base, run fresh CI on its PR snapshot,
verify uploaded evidence, and merge only with the owner's authorization. A real user
feature request should separately exercise the full Agent behavior scenario; static
Skill and fixture checks do not prove that an arbitrary Agent will follow instructions.
No real robot, sensor, navigation stack, physical stop, or actuator was tested here.
