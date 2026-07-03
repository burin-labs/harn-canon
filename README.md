# harn-canon

Seed **invariant** libraries for [Harn Flow](https://github.com/burin-labs/harn). Each pack defines review predicates, evidence, and fixtures that projects can opt into by language or stack.

## What lives here

Per-language and per-stack predicate packs. Each pack is a directory containing:

- `invariants.harn` — Harn functions annotated with `@invariant` and either
  `@deterministic` (pure, 50 ms budget) or
  `@semantic(fallback: predicate_name)` (one cheap LLM judge call, 2 s budget,
  evidence pre-baked at authoring time, plus a same-pack deterministic fallback
  for replay/runtime discovery).
- `README.md` — purpose, stack assumptions, evidence sources, coverage examples, known false positives.
- `fixtures/` — small atom/slice fixtures the predicates are expected to allow or block, used by CI.

`canon-packs.json` is the canonical pack manifest for tools that need stable
pack discovery without scraping the repository layout. It also owns pack
routing metadata: lowercase file extensions and exact lowercase basenames such
as `dockerfile`. Harn and product hosts should infer harn-canon packs from that
manifest instead of carrying their own language-routing tables.

Predicate files use Harn attributes to carry evidence:

```harn
let _EVIDENCE_FLOATING_PROMISES = [
  "https://typescript-eslint.io/rules/no-floating-promises/",
  "https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Promise/catch",
]

@invariant
@deterministic
@archivist(evidence: _EVIDENCE_FLOATING_PROMISES, confidence: 0.9, source_date: "2026-04-24")
pub fn no_floating_promises(slice, _ctx, _repo_at_base) {
  // Predicate body omitted.
}
```

The predicate runtime lives in the [Harn](https://github.com/burin-labs/harn) repo.
This repo tests packs against the Harn release pinned in [`.harn-version`](./.harn-version);
update that file when validating a new runtime.

## Packs

- [C](./c/) — v0 draft predicates for plain C source and headers covering memory, string-handling, format-string, and tempfile footguns.
- [C#](./csharp/) — v0 draft predicates for plain C# and .NET library or application code.
- [C++](./cpp/) — v0 draft predicates for plain C++ application and library code covering memory safety, header hygiene, and special-member discipline.
- [CSS](./css/) — v0 draft predicates for CSS, Sass, and Less stylesheets covering cascade hygiene, internationalization, and accessibility.
- [Dart](./dart/) — v0 draft predicates for Dart application, package, and Flutter source covering null safety, public-API hygiene, async correctness, and widget immutability.
- [Dockerfile](./dockerfile/) — v0 draft predicates for `Dockerfile` and `Containerfile` build recipes.
- [Elixir](./elixir/) — v0 draft predicates for Elixir application and library code on the BEAM.
- [Go](./go/) — v0 draft predicates for Go modules, command packages, and reusable libraries.
- [GraphQL](./graphql/) — v0 draft predicates for GraphQL schema files and the server wiring that hosts them.
- [Harn](./harn/) — v0 draft predicates for `.harn` scripts, Flow workflows, and agent-facing Harn modules.
- [Haskell](./haskell/) — v0 draft predicates for plain Haskell application and library code.
- [HTML](./html/) — v0 draft predicates for plain HTML markup, accessibility, and safe new-window navigation.
- [Java](./java/) — v0 draft predicates for plain Java application and library code.
- [JavaScript](./javascript/) — v0 draft predicates for plain JavaScript source, async handling, dynamic-code hazards, and untrusted data boundaries.
- [JSON](./json/) — v0 draft predicates for strict JSON conformance, encoding hygiene, declared-schema respect, and untrusted-data boundaries.
- [Kotlin](./kotlin/) — v0 draft predicates for Kotlin JVM, Android, and Multiplatform source.
- [Lua](./lua/) — v0 draft predicates for general-purpose Lua application and library code targeting Lua 5.2+ and LuaJIT.
- [Markdown](./markdown/) — v0 draft predicates for prose Markdown files used for documentation, READMEs, and design notes.
- [PHP](./php/) — v0 draft predicates for plain PHP application and library code.
- [Protocol Buffers](./protobuf/) — v0 draft predicates for `.proto` files covering syntax versioning, package hygiene, field numbering, and compatibility.
- [Python](./python/) — v0 draft predicates for Python application and library code.
- [R](./r/) — v0 draft predicates for R analysis scripts, R Markdown / Quarto documents, and R packages.
- [Ruby](./ruby/) — v0 draft predicates for Ruby application and library code.
- [Rust](./rust/) — v0 draft predicates for Rust application and library code.
- [Scala](./scala/) — v0 draft predicates for Scala 2 and Scala 3 source covering null safety, immutability, effect-system hygiene, and pattern-match exhaustiveness.
- [Shell](./shell/) — v0 draft predicates for POSIX shell and Bash scripts covering strict mode, cleanup traps, eval hazards, and ShellCheck discipline.
- [SQL](./sql/) — v0 draft predicates for schema, migration, and query safety.
- [Swift](./swift/) — v0 draft predicates for Swift application and UI code.
- [Terraform](./terraform/) — v0 draft predicates for Terraform configurations across AWS, Azure, and GCP providers.
- [TOML](./toml/) — v0 draft predicates for TOML configuration documents (`Cargo.toml`, `pyproject.toml`, tool configs).
- [TypeScript](./typescript/) — v0 draft predicates for TypeScript and TSX code.
- [XML](./xml/) — v0 draft predicates for XML payloads, XSD schemas, XSLT stylesheets, and related XML-shaped formats.
- [YAML](./yaml/) — v0 draft predicates for plain YAML configuration covering parser footguns and unsafe deserialization tags.
- [Zig](./zig/) — v0 draft predicates for Zig application and library code covering error handling, allocator lifetimes, build metadata, and explicit low-level operations.

## Status

**Early - design-first.** All v0 seed packs are present. The runtime is still evolving in `burin-labs/harn`, so this repo keeps the pack corpus evidence-rich and fixture-backed.

Use this repo to review pack shape, evidence, and fixture coverage independently of runtime work in Harn.

## Contributing

See [CONTRIBUTING.md](./CONTRIBUTING.md). In short: one language per PR, cite evidence ≤18 months old with at least two independent sources (prefer official language/framework docs), and include fixtures.

## License

Dual-licensed under Apache-2.0 and MIT, matching the `harn` repo.
