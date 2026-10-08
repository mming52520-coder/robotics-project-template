# GitHub delivery gates / GitHub 交付门禁

## Read-only baseline (2026-10-08)

The remote `main` was `94bd793`, and open PR #18 (`codex/ros2-simulation-foundation`)
was `1b23621`. This workflow branch starts from the local PR #18 acceptance commit
`c41341f8d586fe03ab5b355a921ec84aafbca79f`, which is not on `main`.
The repository metadata reported `allow_auto_merge=false` and `is_template=false`.
Active ruleset `24631284` (name `main`) targeted the default branch and required only
no deletion and no non-fast-forward update. It listed DeployKey and RepositoryRole
2/4/5 as always-bypass actors. The classic branch-protection endpoint returned 404;
do not infer from that response that no other protections exist. No server setting
was changed while preparing this candidate.

## Rollout after candidate CI is stable

1. Review the final diff, especially `.github/workflows/`, Schemas, validators,
   review policy, and test assertions against a trusted base. Candidate-side success
   alone cannot establish that its own checks remained strong.
2. Confirm PR and ROS CI artifacts contain the manifest, raw logs, and JUnit for the
   final candidate head and tested merge snapshot. The manifest distinguishes those SHAs.
3. Configure the default-branch ruleset to require a pull request and the exact stable
   status-check names `validate-template` and `ros2-simulation`; verify the check source
   and test a blocked merge before treating the rules as effective. Keep auto-merge off.
4. Review the existing always-bypass actors. Remove any AI or automation identity that
   can bypass the main branch. The owner makes the final merge decision. A sole-owner
   repository should not require an impossible second human approval; add human review
   requirements when another maintainer is available.
5. Enable the repository template setting only after the workflow sample is accepted;
   verify a new repository inherits the intended files while leaving secrets, local
   artifacts, hardware values, and remote settings behind.

Keep normal PR jobs read-only, without model credentials or physical device access.
Do not run candidate code in a privileged `pull_request_target` or `workflow_run` job.
Any future credentialed AI review needs a maintainer-controlled trusted workflow that
reads candidate files as untrusted data and does not let candidate rules weaken review.

These are a proposed server-setting rollout and verification procedure, not a claim
that the current GitHub ruleset enforces them.
