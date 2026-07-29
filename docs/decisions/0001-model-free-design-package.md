# ADR-0001: Use model-free DesignBrief and DesignPackage contracts

- Status: accepted
- Date: 2026-07-29
- Owners: repository maintainers

## Context

The template needs to help an AI create reviewable indoor mobile-robot designs without exposing project hardware identities, production data, or executable physical control behavior.

## Decision

Use versioned JSON contracts, five focused project Skills, synthetic examples, and deterministic validation. Keep ROS 2 as a reference architecture, keep hardware output disabled by default, and prohibit vendor/model/part/serial fields in hardware plans.

## Alternatives

- Publish hardware-specific reference implementations: rejected because they couple the public template to private choices and unsafe assumptions.
- Use unstructured prompts only: rejected because required evidence, safety fields, and open decisions cannot be checked deterministically.

## Consequences

The repository produces design and verification plans rather than a bill of materials, hardware driver, or safety certificate. Maintainers must keep examples synthetic and run public-content review before publishing.

## Verification

Run the contract, Skill, evaluation, public-content, unit, lint, and documentation checks in CI.
