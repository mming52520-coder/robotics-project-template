# ADR-0004: Require DesignPackage v2 and executable evidence links

- Status: proposed on the PR #18 acceptance branch
- Date: 2026-10-08
- Owners: repository maintainers

## Context

The v1 package schema accepted empty objects and arbitrary list items in core design sections.
The Python validator checked only a few safety fields. The synthetic packages omitted interface
freshness, measurable acceptance, and links from requirements to executable tests. A passing v1
validation therefore did not establish a complete engineering handoff.

## Decision

Require a versioned v2 DesignPackage while retaining the v1 DesignBrief. Migrate all three
synthetic packages. Require structured interfaces, algorithm and hardware plans, finite safety
limits and timeouts, verification checks, and stable requirement IDs. Implemented requirements
must link to every relevant design entry, ROS interface, source symbol, test ID, and one JUnit
artifact. The validator checks both link directions and can check passing JUnit cases after a
ROS test run. Planned requirements remain explicit without fabricated implementation evidence.

## Consequences

Existing external v1 packages need an explicit migration before validation. Static checks prove
link integrity and contract completeness, not runtime behavior. Four Jazzy ROS tests and JUnit
verification passed locally on the candidate branch. Fresh GitHub CI and its uploaded
JUnit evidence remain a merge gate for this branch.
