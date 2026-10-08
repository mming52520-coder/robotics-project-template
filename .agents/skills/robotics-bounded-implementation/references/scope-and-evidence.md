# Scope and evidence

Run `python3 tools/validate_change_contract.py` before and after editing. If it fails,
reconcile the real diff and the reviewed contract before continuing. The contract validator
does not verify human approval.

The two check scripts generate `artifacts/<run-id>/manifest.json` and raw per-check logs.
The ROS run also records a JUnit digest and test counts. Use
`python3 tools/evidence.py validate artifacts/<run-id>` against the final worktree; a later
file edit makes the earlier evidence stale.
