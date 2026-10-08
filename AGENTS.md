# Agent instructions

## Operating rules

- Read this file, the current work memory, and relevant architecture decisions before editing.
- Separate verified facts, inferences, and unknowns.
- Keep source changes minimal and map each change to an acceptance criterion.
- Preserve raw experiment data and record transformations.
- Run the narrowest relevant test first, then the full project check.
- Update `docs/work-memory/current.md` after a verified change.
- Start robot design work with a validated DesignBrief and complete the five Skills in documented order.
- Before selecting a new reference architecture, run the open-source architecture research Skill and
  retain its sources, open decisions, and license boundary.
- Preserve confirmed, inferred, and open statements separately in every DesignPackage.
- Use a ChangeContract to bound implementation scope and tests; a contract file never proves
  human approval. Keep implementation, evidence review, and final delivery decisions distinct.
- Treat changes to schemas, validators, CI, test assertions, and review policy as core-chain
  changes needing full checks and an independent human review of the candidate diff.

## From a user requirement to reviewed code

When a user asks an Agent working in this checkout to add a feature or fix a defect,
carry the authorized local task through code, tests, and review. Do not stop after a
plan, DesignPackage, ChangeContract, or test proposal unless a concrete blocker remains.

1. Read the request and relevant code, tests, DesignPackage, decisions, and safety paths.
   Reuse an existing validated design for a local change. Create or revise the five-stage
   design only when the requested behavior changes that design.
2. Derive a scoped ChangeContract from the request, with planned requirement and test IDs
   for new behavior. Read `.agents/skills/robotics-change-plan/SKILL.md` and run
   `tools/validate_change_contract.py --phase plan`. The user's development request
   authorizes ordinary local implementation; the Agent must not claim the generated
   contract is separate human approval.
3. Read `.agents/skills/robotics-bounded-implementation/SKILL.md`, then implement
   the behavior and meaningful regression tests in the isolated task branch.
   Update design links to the actual code and tests, then pass the final ChangeContract
   gate and the relevant offline and Jazzy checks. Preserve physical-output and stop gates.
4. Read `.agents/skills/robotics-evidence-review/SKILL.md`; review the entire candidate
   diff and test assertions in a read-only pass against the contract and trusted base.
   Record concrete findings and whether this was a self-review, separate reviewer, or
   OCR. Return confirmed findings to implementation, fix them
   within scope, and rerun affected checks; validate the final evidence snapshot.
5. Deliver the changed code, test evidence, review findings and dispositions, remaining
   risks, and the exact branch or revision. Human merge and hardware decisions remain
   separate. Do not claim an independent review when only self-review ran.

Stop and request a specific decision if the requirement needs unknown safety authority,
physical limits, real hardware access, or a change outside the authorized scope. Keep
working on independent parts of the task while such a decision is pending.

## Safety boundary

- Default to simulation, fake transports, or offline replay.
- Do not command physical hardware without explicit authorization and a documented safe test procedure.
- Do not weaken stop, interlock, limit, watchdog, or fault-recovery behavior to make a test pass.
- Do not commit files from `config/private/`, credentials, customer data, device identifiers, or production endpoints.
- Do not include vendor, model, part number, or serial number in public design artifacts.

## Definition of done

Work is done only when the acceptance criteria pass, evidence is recorded, risks are stated, and working memory is current.
