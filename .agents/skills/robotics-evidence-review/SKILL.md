---
name: robotics-evidence-review
description: Read-only review of a robotics ChangeContract, code diff, test assertions, and bound evidence. Use when a candidate is ready for defect-first independent acceptance review.
---

# Robotics Evidence Review

Read the ChangeContract, DesignPackage, complete candidate diff, and evidence manifests.
Use `references/review-decisions.md` and record findings with
`assets/review-record-template.md` in ignored `artifacts/`. State whether the review
was a separate reviewer, OCR, or the implementing Agent's own read-only pass.

1. Check every changed file against the contract and trusted base. Inspect safety state
   transitions, actual test assertions, and the exact tested snapshot.
2. Run `python3 tools/evidence.py validate artifacts/<run-id>` for each claimed run.
   Missing, failed, skipped, stale, or different-snapshot evidence is not a pass.
3. Classify each finding as confirmed, false positive, duplicate, out of scope, or pending.
   Return confirmed blockers to the implementation stage for a bounded fix and fresh
   regression result. Inspect the new diff and evidence again after a fix.
4. Report the final candidate revision, reviewed file coverage, unresolved findings, and
   human decision still required. Keep model findings separate from deterministic checks.

## Safety and public boundary

- This review pass is read-only. Any fix happens after returning to implementation;
  do not edit here, push, merge, or comment on a PR.
- A self-review is useful but is not independent acceptance of safety or changed checks.
- A model's agreement with another model is not proof of correct robot behavior.
- Never infer physical safety from fake-base zero output or from a complete trace table.
