# Review decisions

For each finding, record a file and line, trigger, violated requirement or invariant,
classification, decision owner, and closure evidence. A suggestion is not a confirmed defect.
Do not keep editing simply to eliminate comments. Two bounded assisted repair rounds are an
upper limit for one review cycle; unresolved issues return to the human reviewer.

The candidate can modify its own validator, CI, and OCR rules. Treat a green candidate run
as observed output, then compare policy changes to the trusted base and require human review
before treating those checks as a merge gate.
