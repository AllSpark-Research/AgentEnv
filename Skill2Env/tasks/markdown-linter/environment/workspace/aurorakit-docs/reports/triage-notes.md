# Support triage notes — docs accuracy (week of 2024-03-18)

Distilled by the support team; please act on these before the 1.0.1 docs
refresh ships.

## T-4821 (2 reports)

Users following the README end up on a GitHub 404. Quote: "clicking
'installation guide' in the project README goes nowhere." Second reporter got
the same from the FAQ link.

## T-4824 (5 reports)

On the Authentication API page, the "token lifetimes" link lands on the CLI
token page — device codes, `aurorakit login` and all that. Our users expected
the HTTP bearer token documentation (lifetimes table, rotation). Please point
that link at the bearer token reference.

## T-4830 (1 report)

A partner reports that "several pages still point at the old 0.9 layout" but
did not list pages. A full sweep of internal links is recommended — the
Docs restructure 1.0 document in this repository is the authoritative map of
what moved.
