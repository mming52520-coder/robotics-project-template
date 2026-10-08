---
name: robotics-change-plan
description: Define a bounded ChangeContract for a specific robotics repository change using an existing DesignPackage. Use before implementation when scope, safety invariants, and required evidence need review.
---

# Robotics Change Plan

Read the current DesignBrief, DesignPackage, work memory, and
`references/change-contract-rules.md`. Use `assets/change-contract-template.json` as a
field guide, then write `changes/<change-id>/change.json`.

1. Identify the actual base revision and the DesignPackage file digest. Keep design-only
   requirements separate from implemented simulation behavior.
2. State the objective, allowed file paths, affected requirement IDs, invariants, required
   test IDs, stop conditions, and explicit exclusions. Link to the design; do not copy it.
3. Run `python3 tools/validate_change_contract.py` and report any uncovered or uncertain
   scope. Validation checks declared consistency, not whether a human approved the plan.
4. Ask for a decision only when the change alters architecture, safety authority, interface
   meaning, or a critical threshold and existing authorization does not cover it.

## Safety and public boundary

- Do not create an approval record, invent test results, or treat `approved: true` as consent.
- Keep physical output disabled and never use live hardware for plan validation.
- Do not include private sites, device identities, credentials, or production endpoints.
