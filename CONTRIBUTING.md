# Contributing to harn-canon

This repo reviews seed invariants carefully. These predicates become the defaults for Harn Flow projects that opt into a stack, so evidence and fixtures matter more than volume.

## Scope per PR

- **One language or stack per PR.** Don't bundle TypeScript + React + Next.js in the same change; split them.
- **5–10 `@deterministic` predicates + 2–3 `@semantic` predicates** is the target bundle for a v0 pack. Less is fine; more should be split.
- **Include fixtures.** Every predicate needs at least one fixture slice it blocks and one it allows. CI runs these.

## Evidence bar

Every `@archivist(...)` attribute must include:

- `evidence: _EVIDENCE_*` - a pack-local evidence constant with at least two independent URLs, no older than **18 months**. Prefer official language/framework/tool docs over blogs.
- `confidence` - `0.0..1.0`, calibrated against the predicate's false-positive rate on fixtures.
- `source_date` - ISO date of the evidence scan.

If you can't meet the evidence bar, file an issue instead and we'll discuss whether to accept a lower-confidence predicate behind a `warn`-only verdict.

## Style

- Use the existing `harn` formatter (`harn fmt`) on changed Harn files when the current formatter can parse them.
- Predicate function names use `snake_case` and describe the rule, not the fix: `no_floating_promises`, not `require_await`.
- Remediation text must be plain English, ≤200 chars, and actionable.

## Review flow

Run `python3 scripts/validate_canon.py` before opening a PR. CI runs the same validator and checks:

- expected pack directories
- root README pack links
- predicate counts and duplicate names
- evidence count and freshness
- fixture shape and allow/block coverage
- pack README coverage for every predicate

Approvals come from CODEOWNERS.

## Proposing a new language / stack

Open an issue with the `area/stack` label and a brief rationale: who uses it, the first predicates to ship, and evidence sources already scoped. Wait for maintainer agreement before starting so drafts do not overlap.

## Licensing

By contributing you agree that your work is licensed under both Apache-2.0 and MIT, matching the parent [`harn`](https://github.com/burin-labs/harn) repo.
