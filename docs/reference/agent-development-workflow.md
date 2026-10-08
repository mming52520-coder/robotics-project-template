# From a local requirement to reviewed code

This repository is meant to be opened in an AGENTS.md-aware coding Agent after cloning.
The user can state a feature or defect in ordinary language. That request starts local
implementation work; the Agent should not stop after generating a plan or listing tests.
The Agent itself needs filesystem and command access to edit and test the checkout.
Repository files constrain that Agent; they do not run a model on their own.

## One-task sequence

1. **Understand:** Read the request, `AGENTS.md`, work memory, relevant DesignPackage,
   existing ROS code and tests, and the safety boundary. Ask only for a decision that
   changes safety authority, unknown physical limits, real hardware access, or scope.
   If the request starts a new robot capability, use the
   [hardware and protocol handoff](hardware-protocol-handoff.md) stages: a private
   selection list and protocol-pending algorithm work can proceed in parallel.
2. **Bound:** Reuse existing design for a local fix. For a new behavior, add planned
   requirement and test IDs through the relevant design Skills. Write one ChangeContract
   and run `python3 tools/validate_change_contract.py --phase plan`.
3. **Build:** Edit the real source and tests in an isolated task branch. Update the
   DesignPackage with actual source symbols, ROS interfaces, test nodes, and evidence
   paths. Run the ChangeContract `--phase final` gate and the offline and Jazzy scripts.
4. **Review:** Inspect the complete changed diff, call sites, safety paths, and test
   assertions in a read-only review pass. Put a review record based on the Skill asset
   under ignored `artifacts/`. Name the reviewer mode honestly: self, separate, or OCR.
5. **Resolve:** Return confirmed defects to implementation, fix within the contract,
   rerun relevant checks, and review the new final snapshot. Report any unresolved
   finding as blocked rather than quietly accepting it.
6. **Deliver:** Give the user the actual code location, branch/revision, checks and
   raw evidence, review findings and dispositions, and unverified risks. Remote push,
   merge, production settings, and physical trials remain separate decisions.

When purchased-device protocols arrive, open a new bounded change for the adapter and
its tests. Reconcile the protocol with the stable ROS contract before coding and keep
the safety gate closed. Passing tests can make the adapter reviewable; physical trial
readiness requires a separate human-reviewed procedure and site preflight.

The plan gate is intentionally usable before a new test has code. The final gate rejects
a planned-only requirement or test. A self-review provides useful defect finding but
does not count as independent approval of safety-critical or checker changes. OCR is
optional; without its installed CLI and verified file coverage, its result is `NOT RUN`.

## Example user request

> Add a read-only timeout diagnostic to the fake base. Keep all motion outputs and stop
> behavior unchanged. Implement it, add meaningful tests, review the diff, and show me
> the final evidence.

The Agent should produce changed source and tests for this request, not a description
of what another builder could do. If the request lacks a measurable acceptance detail,
the Agent can propose and test a reasonable observable behavior while stating its
assumption. If the missing detail affects physical safety, it must stop for a decision.
