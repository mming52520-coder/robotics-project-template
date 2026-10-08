# ADR-0005: Bound AI-assisted changes to design, diff, tests, and evidence

- Status: proposed on `codex/ai-delivery-chain`
- Date: 2026-10-08
- Owners: repository maintainers

## Context

The PR #18 acceptance candidate already has a DesignPackage v2 and bidirectional
requirement links. A static link does not identify which repository revision was tested,
whether a check actually ran, or whether a proposed edit stayed within the intended
scope. Six existing eval fixtures validate declarations; they do not run an Agent.

## Decision

Add one ChangeContract per candidate change, referencing a DesignPackage digest and
listing the base, allowed paths, affected requirements, invariants, and required test IDs.
Use `jsonschema` Draft 2020-12 to validate contract structure; use the existing Python
validators for cross-file and safety semantics. Pin `jsonschema` for repository checks;
install the distribution package in the ROS CI container. ROS runtime nodes remain free
of this development dependency. Preserve v1 package validation only as an explicit
design-only mode; v2 is required for implementation and JUnit claims.

Use the same offline and ROS check scripts locally and in CI. A generated manifest binds
commands, raw logs, JUnit cases, test IDs, hashes of policy/test inputs, actual tested SHA,
candidate head SHA, and any local dirty inputs. A missing, skipped, failed, stale, or
zero-test result blocks acceptance. Keep artifacts ignored locally and upload available
raw evidence from CI even when a check fails.

Add three narrow repository Skills and an optional read-only OCR review wrapper. OCR
suggestions remain unverified until a human checks the finding against the design and
tests. Do not give ordinary PR jobs model credentials or write permission. Never infer
human authorization from a ChangeContract field, passing check, or model review.

## Consequences

Every candidate must have a current ChangeContract and may need a new one after a
different base or scope is selected. Modifying this validator, CI, Schema, review rule,
or test assertion still requires trusted-base inspection and human review because a
candidate can otherwise weaken its own checks. Server-side required PR/check rules
are a separate repository-setting change after the candidate CI has passed. No
hardware or physical-output claim follows from this decision.

For newly requested behavior, the ChangeContract has a `plan` phase that accepts planned
requirement and test IDs with valid links. The Agent can then implement code and tests
without claiming they already exist. The `final` phase requires affected requirements
and required tests to be implemented; only this phase is used by the shared check runner.
The Agent's ordinary local implementation and review follow from the user's development
request, while unresolved safety decisions and external delivery remain separate.
