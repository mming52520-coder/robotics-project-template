# ChangeContract decisions

The DesignPackage describes the system; the ChangeContract limits one edit. Use the current
candidate's `base_revision`, not an old PR head. Every affected implemented requirement
needs an executable test ID. An open decision that blocks that requirement stops the edit.

`allowed_paths` is a review boundary, not permission to make every matching edit. A candidate
can edit its own contract, so a passing validator does not prove authorization. Review the
contract diff against the trusted base and stop when the declared scope changes unexpectedly.

For a new behavior, create planned requirement and test IDs in the DesignPackage, then
run the contract CLI with `--phase plan`. This is enough to begin local code generation
when no blocker remains. After writing code and test nodes, update the package links
and digest, then use `--phase final`; that gate rejects planned-only coverage.
