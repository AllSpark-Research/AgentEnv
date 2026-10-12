# Handoff note — weekend data repair (from Priya)

The nightly ETL corrupted the storefront catalog export again: some prices
landed in the DB as cents, some stock counts went negative, and a few
discontinued items are still flagged active. Finance needs a clean DB and an
audit trail before Monday's reconciliation.

Watch out — product names are full of apostrophes, double quotes, `%`, and
`$`. I tried patching things with inline `python -c "..."` one-liners and the
shell kept mangling the quoting / hanging on input. Write any one-off fixup
logic as a standalone script file you run normally, and read the paths from
`.env` inside the script itself rather than juggling shell variables. Per our
repo hygiene rules, temporary one-off scripts must be prefixed `temp_`, be
covered by `.gitignore`, and be deleted once their results are confirmed —
leave the workspace clean when you're done.
