# Haskell Seed Predicate Pack

This pack covers general-purpose Haskell application and library code. It targets the well-known footguns that an Archivist can catch cheaply on a changed slice: Prelude partial functions in the public API, `undefined` and `error` stubs, unsafe IO escapes, open imports, missing export lists, single-field records that should be `newtype`s, non-exhaustive pattern matches, orphan typeclass instances, and hardcoded secrets.

## Stack Assumptions

- Source files use the `.hs` (Haskell) or `.lhs` (literate Haskell) extension.
- Production paths exclude any path under `test/`, `tests/`, `spec/`, `bench/`, `benches/`, or `examples/`, and any file whose name ends in `Spec.hs`, `Test.hs`, `_spec.hs`, or `_test.hs`.
- "Public API" paths additionally exclude any path under `Internal/`, any module name containing `.Internal.`, and any file ending in `/Internal.hs`. Predicates that should tolerate intentionally unsafe primitives (`no_partial_functions_in_pub_api`) restrict themselves to the public-API set; the `Internal` convention is the standard Haskell escape hatch for partial helpers exposed to maintainers but not callers.
- Deterministic predicates use file-text regex scans because Harn Flow does not yet expose a stable Haskell AST query API; rules with meaningful false-positive risk warn rather than block. Semantic predicates make a single judge call over changed Haskell files.
- Predicates are GHC2024-aware: `total_function_semantic_check` and `prefer_newtype_for_single_field` reflect modern GHC defaults (`-Wincomplete-patterns`, `-Wmissing-export-lists`, `-Wmissing-import-lists`).

## Predicate Coverage

| Predicate | Mode | Verdict | Purpose |
|---|---|---|---|
| `no_partial_functions_in_pub_api` | deterministic | Block | Prelude partials (`head`, `tail`, `init`, `last`, `fromJust`, `(!!)`) crash on edge cases callers cannot anticipate. |
| `no_undefined_in_prod` | deterministic | Block | `undefined` is a placeholder; shipping it crashes the program at the first use. |
| `no_error_call_in_prod` | deterministic | Warn | `error "..."` raises a non-recoverable `ErrorCall` instead of a typed value or exception callers can handle. |
| `no_unsafe_perform_io` | deterministic | Block | `unsafePerformIO`/`unsafeInterleaveIO`/`unsafeFixIO` break referential transparency and the strictness analyser's assumptions. |
| `explicit_imports` | deterministic | Warn | Open imports leak the entire downstream namespace into scope, masking conflicts and slowing review. |
| `explicit_export_list` | deterministic | Warn | Modules without an export list expose every binding as public surface, blocking safe refactors. |
| `prefer_newtype_for_single_field` | deterministic | Warn | A single-constructor, single-field record is `newtype`-able for zero runtime overhead and a stricter representation. |
| `total_function_semantic_check` | semantic | Block | Functions whose pattern matches are non-exhaustive crash at runtime when an unhandled constructor flows through. |
| `no_orphan_instances` | semantic | Block | Orphan instances make typeclass coherence depend on import order and break compositional reasoning. |
| `no_hardcoded_secrets` | semantic | Block | Credentials embedded in source leak through commits, build artefacts, and error messages. |

## Evidence

Evidence scanned on 2026-05-10.

- GHC user guide: `using-warnings.html` (`-Wincomplete-patterns`, `-Wmissing-import-lists`, `-Wmissing-export-lists`, `-Worphans`, `-Wx-partial`) and the FFI/extensions chapters covering `unsafePerformIO`.
- Hackage `base` reference: `Prelude` (`head`, `tail`, `init`, `last`, `undefined`, `error`), `Data.Maybe.fromJust`, `System.IO.Unsafe`, and `Control.Exception` for typed exception handling.
- Haskell Wiki: `Avoiding_partial_functions`, `Newtype`, and `Orphan_instance` community guidance pages.
- HLint: hint catalogue covering partial functions, single-field records, and import discipline.
- Haskell 2010 Report §5: module export lists and visibility semantics.
- OWASP Cheat Sheet Series and GitHub secret-scanning documentation: hardcoded-credential risk and remediation patterns.

## Known False Positives

- Regex predicates do not parse Haskell. Comments, string literals, Template Haskell quasi-quotes, and identifier ticks (`head'`) can fool the deterministic checks until AST-backed matching lands.
- `no_partial_functions_in_pub_api` flags bare uses of `head`/`tail`/`init`/`last`/`fromJust` and the `(!!)` operator. Fully qualified references (`Data.List.head`) are not caught because the leading `.` confuses the boundary heuristic; qualified `Prelude` partials are rare in practice because `Prelude` is auto-imported. Move legitimate partial helpers into an `Internal` module to suppress the rule.
- `no_undefined_in_prod` flags every occurrence of the `undefined` token. Shadowed local `undefined` bindings (rare) are a false positive.
- `no_error_call_in_prod` matches `error "..."`, `error [...]`, and `error show ...` but does not parse expression context, so an `error` call inside a Template Haskell splice or a quasi-quoted string can be flagged.
- `no_unsafe_perform_io` flags any reference to the listed identifiers, including type signatures and re-exports. Wrap legitimate uses in an `Internal` module or a clearly-named `unsafe*` helper.
- `explicit_imports` only inspects single-line `import` statements that fit on one line; multi-line imports with the parenthesised list on a follow-up line are out of scope until AST queries land.
- `explicit_export_list` matches `module Foo where` on a single line and tolerates Haddock comments before `module`. Modules whose `where` keyword is on a separate line from the module name are treated as having an export list and are not flagged.
- `prefer_newtype_for_single_field` only matches the single-line, single-field record syntax `data X = X { f :: T }`; multi-line records and positional single-field types (`data X = X T`) are not flagged because they overlap with sum-type stubs that often grow more constructors.
- `total_function_semantic_check` and `no_orphan_instances` are conservative semantic checks. Until Flow exposes structured Haskell data, the judge can miss matches that span imports it cannot see.

## Fixtures

Each fixture in `fixtures/` contains one blocked or warned example and one allowed example for the corresponding predicate. The fixture shape mirrors the existing seed packs:

```json
{
  "predicate": "name",
  "cases": [
    {"expect": "Block", "files": [{"path": "src/Foo.hs", "text": "..."}]},
    {"expect": "Allow", "files": [{"path": "src/Foo.hs", "text": "..."}]}
  ]
}
```
