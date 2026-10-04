# Docs restructure 1.0 ("Constellation") — authoritative move map

This is the authoritative record of every path changed by the March 2024
documentation restructure (PR aurorakit/aurorakit#612). Published URLs must
redirect according to this table, and internal links must point at the new
locations.

## Move history

| Old path (0.9)                      | New path (1.0)                       |
| ----------------------------------- | ------------------------------------ |
| docs/getting-started/installation.md | docs/guides/install.md              |
| docs/legacy/faq.md                  | docs/guides/troubleshooting.md       |
| docs/guides/quickstart.md           | docs/guides/start-here.md            |
| docs/style-guide.md                 | docs/style/editorial-guide.md        |
| .github/ISSUE_TEMPLATE/bug-report.md | templates/bug-report.md             |
| docs/reference/error-codes.md       | docs/api/error-codes.md              |
| docs/guides/config-schema.md        | docs/api/config-schema.md            |
| docs/images/architecture.png        | docs/images/architecture-overview.png |
| docs/oncall.md                      | docs/ops/oncall-guide.md             |
| docs/migration-guide.md             | docs/migration/moves-1.0.md          |

## Editorial decisions in 1.0

- All filenames under `docs/api/` are lower-case. A few pages still carry
  old-style references with an upper-case directory or file name; treat those
  as stale and update them when touched.
- The former combined token page was split into two documents:
  `docs/api/auth-tokens.md` (HTTP bearer tokens: scopes, lifetimes, rotation)
  and `docs/api/cli-tokens.md` (CLI device-code sessions). When a page
  discusses the HTTP API, its links must go to the bearer document; when it
  discusses the CLI, to the CLI document. The two files are similar on
  purpose — check before linking.
- No 0.9 path was kept on disk; there are no legacy shim files to link to.
