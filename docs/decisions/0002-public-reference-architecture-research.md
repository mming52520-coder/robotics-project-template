# ADR-0002: Research public architecture references before bespoke design

- Status: accepted
- Date: 2026-08-03
- Owners: repository maintainers

## Context

Early robot and embedded projects often rebuild architecture patterns that already have public,
well-maintained references. The template needs a repeatable way to inspect the current project,
compare relevant public repositories, and document why an architecture pattern is adopted without
copying source code or private project details.

## Decision

Provide a project-local Skill that extracts non-private architecture signals, searches or ranks
public GitHub metadata, scores candidates by relevance before stars, and records public README
evidence in a deterministic research report. An AI then produces a separate, traceable architecture
recommendation from that evidence and the bundled template. Keep generated research artifacts
ignored by default. Use only standard-library Python and anonymous public API access; on rate
limits, use a host search capability with explicit source records instead of embedding a token.

## Alternatives

- Start from a blank architecture: rejected because it discards proven public patterns and hides
  reference-selection assumptions.
- Select the repository with the highest star count: rejected because stars do not establish fit,
  safety, maintenance quality, or license compatibility.
- Clone a reference repository into the project: rejected because it creates licensing, provenance,
  security, and model-specific coupling risks.

## Consequences

Architecture recommendations become evidence-backed inputs to local design, not implementation
authority. Candidates remain subject to manual documentation review, license review, local
simulation, verification, and human safety review. The new Skill does not collect credentials or
request access to private repositories.

## Verification

Run unit tests for local inspection, candidate ranking, report rendering, and rate-limit fallback
ranking. Run the project validation suite and the Skill validator.
