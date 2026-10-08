---
name: robotics-evidence-review
description: Read-only review of a robotics ChangeContract, code diff, test assertions, and bound evidence. Use when a candidate is ready for defect-first independent acceptance review.
---

# Robotics Evidence Review

Read the ChangeContract, DesignPackage, complete candidate diff, and evidence manifests.
Use `references/review-decisions.md`. Run `python3 tools/review_coverage.py create`
after the final source edit and checks; it writes an ignored `artifacts/review-*/record.json`
with the exact changed-file inventory and snapshot. Use `assets/review-record-template.md`
for the fields to fill. State whether the review was by a separate reviewer, OCR, or
the implementing Agent's own read-only pass.

1. Check every `changed_paths` entry against the contract and trusted base. Inspect
   safety state transitions, actual test assertions, and the exact tested snapshot.
   Include both sides of renames and index-only staged paths. If index and worktree
   bytes diverge, resolve that state before treating test evidence as acceptance.
   Fill `reviewed_paths` only after inspecting each path. Put unresolved or filtered
   paths in `skipped_paths` with reasons; validation will keep the review blocked.
2. Run `python3 tools/evidence.py validate artifacts/<run-id>` for each claimed run.
   Missing, failed, skipped, stale, or different-snapshot evidence is not a pass.
3. Classify each finding as confirmed, false positive, duplicate, out of scope, or pending.
   Record path, line, violated contract, trigger, status, disposition, and regression
   reference. Return confirmed blockers to implementation for a bounded fix and fresh
   regression result. Inspect the new diff and evidence again after a fix.
4. Fill `evidence_runs.offline` and `evidence_runs.ros` with the current ignored run
   directories, then run `python3 tools/review_coverage.py validate <record.json>`.
   Their base, head, and ChangeContract must match the reviewed candidate.
   Report the candidate revision, covered files, unresolved findings, and human decision
   still required. A successful JSON check cannot establish independent or human review.

## Safety and public boundary

- This review pass is read-only. Any fix happens after returning to implementation;
  do not edit here, push, merge, or comment on a PR.
- A self-review is useful but is not independent acceptance of safety or changed checks.
- A model's agreement with another model is not proof of correct robot behavior.
- Never infer physical safety from fake-base zero output or from a complete trace table.
