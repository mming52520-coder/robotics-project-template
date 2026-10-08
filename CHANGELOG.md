# Changelog

## [0.2.0] - 2026-07-29

### Added

- Versioned DesignBrief and DesignPackage contracts for model-free indoor wheeled-robot design.
- Five ROS 2 reference Skills for system design, navigation, hardware, safety, and verification.
- Synthetic positive design packages, safety-blocking evaluation cases, and deterministic validators.
- Public-content scanning for credentials and hardware-identifying fields.

All notable changes follow semantic versioning.

## [Unreleased]

### Added

- DesignPackage v2 with required interface, safety, verification, and bidirectional
  requirement-to-evidence links; all synthetic packages migrated from v1.
- Simulation gate startup and restart fail closed until an explicit safe reset.
- JUnit evidence verification for implemented ROS checks.
- Public open-source architecture research Skill with local project inspection, high-star candidate
  scoring, source evidence, rate-limit fallback, and a no-code-copy boundary.
- Simulation-only ROS 2 Jazzy package with bounded motion gating, a fake base, synthetic fault
  injection, installed launch, offline tests, and ROS runtime CI.

## [0.1.0] - 2026-07-29

### Added

- Robotics and embedded project structure.
- Agent operating and hardware-safety rules.
- Architecture, decision, experiment, and working-memory templates.
- Public and private configuration separation.
- Unit, integration, and replay test scaffolding.
- CI checks for structure, Markdown, YAML, Python, shell, and public-release safety.
