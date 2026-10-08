# ADR-0006: Separate private hardware handoff from public design

- Status: proposed
- Date: 2026-10-08
- Owners: repository maintainers

## Context

ADR-0001 keeps the public DesignPackage model-free. A project team also needs a
concrete purchase comparison, then a way to supply the received device protocol to
an Agent without making up a driver or publishing private facts. The current ROS
package has only a fake base and no verified device contract.

## Decision

Retain the public capability and trace contracts. Put candidate selection and received
protocol evidence in ignored `config/private/`, linked by public requirement and
interface IDs. Permit algorithm work through stable ROS interfaces and fake/replay
transport while device details are pending. After protocol receipt, require a reviewed
adapter and offline evidence before a separately authorized physical trial. Protocol
receipt never grants actuation authority. The public template does not include a
device driver or product recommendation.

The public-content checks ignore only private files that Git actually ignores; a
force-tracked private file remains a validation failure. Project-specific adapter code
may be versioned in a separately controlled project repository, subject to that
project's review policy, while secrets and unit identities stay out of source control.

## Verification and limits

The local Git-ignore behavior has a regression test. The workflow has no real product,
protocol, hardware, calibration, or site evidence yet. Physical trial readiness remains
`BLOCKED` until a responsible engineer approves a documented safe procedure.
