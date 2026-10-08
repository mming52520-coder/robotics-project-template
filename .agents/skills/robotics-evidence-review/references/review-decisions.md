# Review decisions

For each finding, record a file and line, trigger, violated requirement or invariant,
classification, decision owner, and closure evidence. A suggestion is not a confirmed defect.
Do not keep editing simply to eliminate comments. Two bounded assisted repair rounds are an
upper limit for one review cycle; unresolved issues return to the human reviewer.

The candidate can modify its own validator, CI, and OCR rules. Treat a green candidate run
as observed output, then compare policy changes to the trusted base and require human review
before treating those checks as a merge gate.
When the implementing Agent performs the review itself, label it self-review and record
which changed paths and assertions it actually inspected. Do not label it independent.
Keep the review record in ignored `artifacts/` so recording findings does not stale the
source snapshot manifest.
