# harn-canon

Seed **invariant** libraries for [Harn Flow](https://github.com/burin-labs/harn) — the agent-native shipping substrate built into the [Harn language](https://github.com/burin-labs/harn).

> A repo's *canon* is the living body of best practices it expects changes to respect. The Archivist persona authors the canon. The Ship Captain persona enforces it.

## What lives here

Per-language and per-stack **starter predicate packs** that any project can opt into. Each pack is a directory containing:

- `invariants.harn` — Harn functions annotated with `@invariant` and either `@deterministic` (pure, 50 ms budget) or `@semantic` (one cheap LLM judge call, 2 s budget, evidence pre-baked at authoring time).
- `README.md` — purpose, stack assumptions, evidence sources, coverage examples, known false positives.
- `fixtures/` — small atom/slice fixtures the predicates are expected to allow or block, used by CI.

Predicate files use Harn attributes to carry evidence:

```harn
@invariant
@deterministic
@archivist(
  evidence = ["https://typescript-eslint.io/rules/no-floating-promises/"],
  confidence = 0.9,
  source_date = "2026-04-24",
)
fn no_floating_promises(slice: Slice, ctx: Context, repo_at_base: Repo) -> InvariantResult {
  // …
}
```

See the Harn Flow design docs for the full predicate language spec.

## Packs

- [C#](./csharp/) — v0 draft predicates for plain C# and .NET library or application code.
- [CSS](./css/) — v0 draft predicates for CSS, Sass, and Less stylesheets covering cascade hygiene, internationalization, and accessibility.
- [Go](./go/) — v0 draft predicates for Go modules, command packages, and reusable libraries.
- [Harn](./harn/) — v0 draft predicates for `.harn` scripts, Flow workflows, and agent-facing Harn modules.
- [Java](./java/) — v0 draft predicates for plain Java application and library code.
- [JavaScript](./javascript/) — v0 draft predicates for plain JavaScript source, async handling, dynamic-code hazards, and untrusted data boundaries.
- [JSON](./json/) — v0 draft predicates for strict JSON conformance, encoding hygiene, declared-schema respect, and untrusted-data boundaries.
- [Kotlin](./kotlin/) — v0 draft predicates for Kotlin JVM, Android, and Multiplatform source.
- [Python](./python/) — v0 draft predicates for Python application and library code.
- [Ruby](./ruby/) — v0 draft predicates for Ruby application and library code.
- [Rust](./rust/) — v0 draft predicates for Rust application and library code.
- [SQL](./sql/) — v0 draft predicates for schema, migration, and query safety.
- [Swift](./swift/) — v0 draft predicates for Swift application and UI code.
- [TOML](./toml/) — v0 draft predicates for TOML configuration documents (`Cargo.toml`, `pyproject.toml`, tool configs).
- [TypeScript](./typescript/) — v0 draft predicates for TypeScript and TSX code.
- [XML](./xml/) — v0 draft predicates for XML payloads, XSD schemas, XSLT stylesheets, and related XML-shaped formats.

## Status

🚧 **Early — design-first.** The predicate language, `InvariantResult` type, and runtime harness are still being specified in `burin-labs/harn`. This repo exists now to:

1. Reserve the namespace and let contributors start drafting seed predicates.
2. Collect evidence and discussion per-language independently of the core substrate schedule.
3. Surface a clear contribution path: pick a language, draft 5–10 deterministic + 2–3 semantic predicates, open a PR.

## Contributing

See [CONTRIBUTING.md](./CONTRIBUTING.md). In short: one language per PR, cite evidence ≤18 months old with at least two independent sources (prefer official language/framework docs), and include fixtures.

## License

Dual-licensed under Apache-2.0 and MIT, matching the `harn` repo.
