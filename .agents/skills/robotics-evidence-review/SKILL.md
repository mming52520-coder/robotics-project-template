---
name: robotics-evidence-review
description: Read-only review of a robotics ChangeContract, code diff, test assertions, and bound evidence. Use when a candidate is ready for defect-first independent acceptance review.
---

# Robotics Evidence Review

Read the ChangeContract, DesignPackage, candidate diff, and evidence manifest. Use
`references/review-decisions.md` and record findings with `assets/review-record-template.md`.

1. Check every changed file against the contract and trusted base. Inspect safety state
   transitions, actual test assertions, and the exact tested snapshot.
2. Run `python3 tools/evidence.py validate artifacts/<run-id>` for each claimed run.
   Missing, failed, skipped, stale, or different-snapshot evidence is not a pass.
3. Classify each finding as confirmed, false positive, duplicate, out of scope, or pending.
   A confirmed blocker needs a bounded fix and a fresh regression result.
4. Report the final candidate revision, reviewed file coverage, unresolved findings, and
   human decision still required. Keep model findings separate from deterministic checks.

## Safety and public boundary

- Review only; do not edit source, auto-fix, push, merge, or comment on a PR.
- A model's agreement with another model is not proof of correct robot behavior.
- Never infer physical safety from fake-base zero output or from a complete trace table.
