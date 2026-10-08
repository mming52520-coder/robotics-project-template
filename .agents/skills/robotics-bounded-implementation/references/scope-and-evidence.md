# Scope and evidence

Run `python3 tools/validate_change_contract.py --phase plan` before editing and
`python3 tools/validate_change_contract.py --phase final` after code and tests exist.
If either fails, reconcile the real diff and contract before continuing. The validator
does not verify human approval.

The two check scripts generate `artifacts/<run-id>/manifest.json` and raw per-check logs.
The ROS run also records a JUnit digest and test counts. Use
`python3 tools/evidence.py validate artifacts/<run-id>` against the final worktree; a later
file edit makes the earlier evidence stale.
After the checks, continue into a read-only diff review. Fix confirmed defects back in
the implementation stage and regenerate both the checks and review for the final snapshot.
