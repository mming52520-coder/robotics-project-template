---
name: robotics-change-plan
description: Turn a user's robotics feature or fix request into a bounded ChangeContract and continue toward implementation. Use when scope, safety invariants, and required evidence must be linked to a DesignPackage.
---

# Robotics Change Plan

Read the user's requested behavior, current DesignBrief, DesignPackage, work memory, and
`references/change-contract-rules.md`. Use `assets/change-contract-template.json` as a
field guide, then write `changes/<change-id>/change.json`. A normal local development
request authorizes continuing into implementation; do not ask for a second generic
confirmation after creating the contract.

1. Identify the actual base revision and DesignPackage digest. Reuse existing design
   when it covers the request; revise the relevant design stages when behavior is new.
   Keep planned requirements separate from implemented simulation behavior.
2. State the objective, allowed file paths, affected requirement IDs, invariants, required
   test IDs, stop conditions, and explicit exclusions. Link to the design; do not copy it.
3. Run `python3 tools/validate_change_contract.py --phase plan`. Planned tests may
   reserve stable IDs at this point. Validation checks declared consistency, not human
   approval or completed code. Continue to `robotics-bounded-implementation` in the
   same user task when no blocking decision remains.
4. Ask for a decision only when the change alters architecture, safety authority, interface
   meaning, or a critical threshold and existing authorization does not cover it.

## Safety and public boundary

- Do not create an approval record, invent test results, or treat `approved: true` as consent.
- Keep physical output disabled and never use live hardware for plan validation.
- Do not include private sites, device identities, credentials, or production endpoints.
