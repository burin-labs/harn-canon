# AGENTS.md

This repo stores Harn canon seed predicate packs. Keep changes small, explicit,
and evidence-backed.

## Repo shape

- Each pack lives at the repo root, for example `rust/`, `typescript/`, or
  `harn/`.
- A pack contains `invariants.harn`, `README.md`, and `fixtures/*.json`.
- `scripts/validate-canon.harn` is the local and CI structure gate.
- `docs/` is only an index for shared policy and design notes. Pack-specific
  rationale belongs in the pack README.

## Editing rules

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

- Structure and fixtures:
  `harn run scripts/validate-canon.harn -- --today $(date -u +%F)`
- Deterministic fixtures: `harn run scripts/execute-fixtures.harn`
- Package boundary tests: `harn test tests/`
- Strict source gate: `harn check --strict-types . && harn lint --strict .`
- Typed Flow capability boundary:
  `harn run --no-sandbox scripts/assert-flow-capability-contract.harn`
- Validator syntax:
  `harn check scripts/canon-lib.harn scripts/validate-canon.harn scripts/execute-fixtures.harn scripts/assert-flow-capability-contract.harn tests/canon-boundary.harn`
- Whitespace: `git diff --check`
- Harn formatting: run `harn fmt --check <changed .harn files>` when touching
  Harn files. Do not treat repo-wide `harn fmt --check .` as a clean gate until
  the existing formatter limitations are fixed.

## Git

- Work on an isolated branch or worktree.
- Rebase on `origin/main` before opening a PR.
- Keep PRs focused. One language or stack per behavior change remains the
  default shape for predicate work.
- Title pull requests `[Area] Sentence case summary`, where the area is the
  pack directory or `core` for validator, manifest, and CI work. See
  [CONTRIBUTING.md](CONTRIBUTING.md).

<!-- BEGIN HARN SHARED AGENT CONTRACT: managed by harn-bump-fleet -->

## Ecosystem working agreement

- Build ambitious outcomes behind small typed interfaces; give behavior one owner
  and generate or parity-test projections instead of duplicating policy.
- Work autonomously within approved scope. Pause for destructive or production effects,
  exceptional spend, material ambiguity, or new authority.
- Treat stop, wait, stand down, pivot, and steer as control events.
- Use the smallest owning product-path check. Add a falsifier for contested, load-bearing,
  or potentially vacuous claims; record controls, recovery, and blind spots.
- Evidence follows source/artifact identity. Reuse proof when relevant code, build inputs,
  and dependencies are unchanged. Repeat affected checks for relevant changes, failures,
  deployment, or packaging differences. Do not rebuild or recapture solely for main.
- Ship means owning-main integration with terminal merge and applicable release/deploy
  checks. Confirm landed content and result; an open PR is incomplete.
- Use `ship` with a deployed Smart Ship caller; otherwise use `gh pr merge --squash --auto`.
  Never use `--admin`; incidents use `bypass-ci`, `bypass-merge-queue`, or `force-merge`.

<!-- END HARN SHARED AGENT CONTRACT -->
