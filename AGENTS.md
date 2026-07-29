# Agent instructions

## Operating rules

- Read this file, the current work memory, and relevant architecture decisions before editing.
- Separate verified facts, inferences, and unknowns.
- Keep source changes minimal and map each change to an acceptance criterion.
- Preserve raw experiment data and record transformations.
- Run the narrowest relevant test first, then the full project check.
- Update `docs/work-memory/current.md` after a verified change.
- Start robot design work with a validated DesignBrief and complete the five Skills in documented order.
- Preserve confirmed, inferred, and open statements separately in every DesignPackage.

## Safety boundary

- Default to simulation, fake transports, or offline replay.
- Do not command physical hardware without explicit authorization and a documented safe test procedure.
- Do not weaken stop, interlock, limit, watchdog, or fault-recovery behavior to make a test pass.
- Do not commit files from `config/private/`, credentials, customer data, device identifiers, or production endpoints.
- Do not include vendor, model, part number, or serial number in public design artifacts.

## Definition of done

Work is done only when the acceptance criteria pass, evidence is recorded, risks are stated, and working memory is current.
