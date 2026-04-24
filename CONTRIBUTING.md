# Contributing to harn-canon

Thanks for contributing seed invariants! This repo intentionally moves slowly and reviews evidence carefully — the predicates here become the *defaults* shipped to every Harn Flow user opting into a stack, so quality matters more than quantity.

## Scope per PR

- **One language or stack per PR.** Don't bundle TypeScript + React + Next.js in the same change; split them.
- **5–10 `@deterministic` predicates + 2–3 `@semantic` predicates** is the target bundle for a v0 pack. Less is fine; more should be split.
- **Include fixtures.** Every predicate needs at least one fixture slice it blocks and one it allows. CI runs these.

## Evidence bar

Every `@archivist(...)` attribute must include:

- `evidence = [urls]` — at least two independent sources, no older than **18 months**. Prefer official language/framework/tool docs over blogs. Dead-link check runs in CI.
- `confidence` — `0.0..1.0`, calibrated against the predicate's false-positive rate on fixtures.
- `source_date` — ISO date of the evidence scan.

If you can't meet the evidence bar, file an issue instead and we'll discuss whether to accept a lower-confidence predicate behind a `warn`-only verdict.

## Style

- Use the existing `harn` formatter (`harn fmt`). Pre-commit hook in this repo enforces it once the toolchain lands.
- Predicate function names use `snake_case` and describe the rule, not the fix: `no_floating_promises`, not `require_await`.
- Remediation text in `InvariantResult` must be plain English, ≤200 chars, and actionable.

## Review flow

All PRs go through the merge queue. Required checks: fmt, lint, evidence-link validation, fixture replay. Approvals: at least one CODEOWNERS reviewer.

## Proposing a new language / stack

Open an issue with the `area/stack` label and a brief rationale (who uses it, what the killer 5 predicates would be, evidence sources you've already scoped). Get a 👍 from a maintainer before starting — this avoids overlapping drafts.

## Licensing

By contributing you agree that your work is licensed under both Apache-2.0 and MIT, matching the parent [`harn`](https://github.com/burin-labs/harn) repo.
