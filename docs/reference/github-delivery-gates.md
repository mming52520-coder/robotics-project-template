# GitHub delivery gates / GitHub 交付门禁

## Read-only state on 2026-10-09

`main` is `ba2227d`; PR #20 and PR #21 merged in order, and both main-push CI
runs passed their offline and Jazzy jobs. The governance delivery branch starts
at that main commit. At the 2026-10-09 local acceptance checkpoint, its
repository-side final gate had not run on remote CI; inspect the current PR
checks before any merge decision.

`gh api repos/mming52520-coder/robotics-project-template/rulesets/24631284`
confirmed the active default-branch ruleset. Its only
rules are deletion and non-fast-forward prevention. It grants always-bypass to
DeployKey and RepositoryRole 2/4/5; the API reports the current account can bypass.
An earlier classic `branches/main/protection` read returned
`404 Branch not protected`; the later independent re-audit received `403`.
These reads do not prove there are no organization or enterprise controls. The
repository currently reports `allow_auto_merge=false` and `is_template=false`.
No settings were changed in this task.

## Minimal settings delta, after separate owner authorization

1. Keep the existing deletion and non-fast-forward rules. Add a required pull
   request rule for `main`; do not require an impossible second human reviewer in
   a single-maintainer repository. The owner must still decide each merge.
2. Require these exact CI status names from the `CI` workflow on the candidate's
   final tested merge: `validate-template`, `ros2-simulation`, and
   `final-acceptance`. Confirm the expected GitHub Actions source in the settings UI
   before saving. Require the branch to be current with its target so stale base
   evidence reruns. Preserve read-only `pull_request` execution with no model secrets
   or physical device access; do not switch to privileged `pull_request_target` or
   `workflow_run` execution of candidate code.
3. Remove or narrow bypass entries that permit AI or automation identities to
   merge around these checks. Review DeployKey and repository-role mappings against
   actual actors before changing them; current API data alone does not identify
   which identities use each role. Retain only the emergency owner path the owner
   explicitly chooses and records. A JSON review `reviewer_mode` value is never
   proof of a reviewer or approval.

The impact is that ordinary direct pushes and PRs without passing checks will be
blocked. A PR without the v2 review record, fresh unit/ROS artifacts, and complete
coverage should fail `final-acceptance`. The first PR run can upload a v2 review
template for its exact merged snapshot; editing the PR body reruns the checks.

Before calling this effective, inspect the saved ruleset with `gh api`, verify the
three required check names and sources, then attempt a harmless blocked merge or
equivalent ruleset evaluation with the owner in a controlled test. Record a case
missing the final check and a case with a failed final check. Inspect bypass audit
events if available. Restore the previous ruleset JSON and actor list through the
settings UI or API if the new rule prevents normal maintenance; keep the read-only
baseline captured above as the rollback reference. Do not claim an actual blocked
merge from local tests or a settings proposal.
