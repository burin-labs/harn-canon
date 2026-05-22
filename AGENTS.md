# AGENTS.md

This repo stores Harn canon seed predicate packs. Keep changes small, explicit,
and evidence-backed.

## Repo Shape

- Each pack lives at the repo root, for example `rust/`, `typescript/`, or
  `harn/`.
- A pack contains `invariants.harn`, `README.md`, and `fixtures/*.json`.
- `scripts/validate_canon.py` is the local and CI structure gate.
- `docs/` is only an index for shared policy and design notes. Pack-specific
  rationale belongs in the pack README.

## Editing Rules

- Keep `invariants.harn`, the pack README, and fixtures in lockstep. Every
  predicate needs a matching fixture file and a README row.
- Preserve the `@archivist(evidence: _EVIDENCE_*, confidence: ...,
  source_date: "...")` shape.
- Evidence constants need at least two independent URLs and a `source_date`
  within 18 months.
- Do not hand-wave runtime behavior. Name the current limitation and the
  exact predicate or harness that owns it.
- Prefer direct prose in the spirit of slopwash.com: concrete nouns, short
  sentences, no inflated positioning, no filler summaries.

## Validation

- Structure and fixtures: `python3 scripts/validate_canon.py`
- Validator syntax: `python3 -m py_compile scripts/validate_canon.py`
- Whitespace: `git diff --check`
- Harn formatting: run `harn fmt --check <changed .harn files>` when touching
  Harn files. Do not treat repo-wide `harn fmt --check .` as a clean gate until
  the existing formatter limitations are fixed.

## Git

- Work on an isolated branch or worktree.
- Rebase on `origin/main` before opening a PR.
- Keep PRs focused. One language or stack per behavior change remains the
  default shape for predicate work.
