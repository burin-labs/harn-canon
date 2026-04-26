# Rust Seed Predicate Pack

This pack covers Rust crates and workspaces. It targets high-signal issues that are cheap to catch from changed source slices: accidental panics, undocumented unsafe code, blocking work in async functions, dependency-advisory drift, and public API contracts that callers can otherwise misuse.

## Stack Assumptions

- Rust source files use `.rs`; Cargo metadata uses `Cargo.toml` and `Cargo.lock`.
- Production paths exclude `tests/`, `benches/`, and `examples/` fixtures or sample programs.
- Deterministic predicates operate on changed file text until Harn Flow exposes a stable Rust AST query API.
- Semantic predicates make one cheap judge call over changed Rust/Cargo files and use only evidence captured at authoring time.
- The pack is advisory-first where regex matching has likely false positives. Blocking rules are reserved for unfinished code, bare production unwraps, undocumented unsafe blocks, obvious blocking calls inside `async fn`, and missing semantic dependency/FFI safety evidence.

## Predicate Coverage

| Predicate | Mode | Verdict | Purpose |
|---|---|---|---|
| `no_unwrap_in_prod` | deterministic | Block | Bare `unwrap`/`unwrap_err` in production Rust should not ship without explicit handling or a named invariant. |
| `must_use_message_on_pub_result_option` | deterministic | Warn | Public `Result`/`Option`-returning functions should add a custom unused-value message when the default warning lacks domain context. |
| `unsafe_requires_safety_comment` | deterministic | Block | Each unsafe block or impl needs a nearby `// SAFETY:` justification. |
| `no_blocking_io_in_async` | deterministic | Block | `async fn` bodies should not call obvious blocking std APIs directly. |
| `no_dbg_macro_in_prod` | deterministic | Warn | `dbg!` is a temporary debugging macro and should not be committed to production paths. |
| `no_todo_or_unimplemented_in_prod` | deterministic | Block | `todo!` and `unimplemented!` mark unfinished production code. |
| `no_wildcard_imports_in_prod` | deterministic | Warn | Module-level glob imports can obscure name provenance and produce surprising shadowing. |
| `no_panic_in_result_fn` | deterministic | Warn | `Result`-returning functions should usually return `Err` or document panic behavior. |
| `cargo_advisories_checked` | semantic | Block | Dependency changes should preserve or run RustSec/cargo-audit/cargo-deny-style advisory checks. |
| `ffi_boundary_safety_contract` | semantic | Block | Public FFI and unsafe wrappers need explicit safety, ownership, nullability, and lifetime contracts. |

## Evidence

Evidence scanned on 2026-04-26.

- Rust Clippy lint docs: `unwrap_used`, `must_use_candidate`, `undocumented_unsafe_blocks`, `dbg_macro`, `todo`, `unimplemented`, `wildcard_imports`, `panic_in_result_fn`, and `missing_panics_doc`.
- Rust Reference and Edition Guide: `#[must_use]`, `unsafe` proof obligations, glob imports, and Rust 2024 unsafe extern blocks.
- Rust By Example and standard library docs: `Option`/`Result` unwrap behavior and debugging/unfinished-code macros.
- Tokio and Async Book docs: blocking work in async contexts, `spawn_blocking`, and async `sleep`.
- RustSec, cargo-deny, and Cargo docs: advisory databases, dependency checks, and `Cargo.lock` reproducibility.

## Known False Positives

- Regex predicates do not parse Rust. Macro-generated functions, nested blocks, raw strings, comments, and multi-line signatures can confuse the deterministic checks.
- `no_unwrap_in_prod` ignores test, bench, and example paths, but it can still catch intentional invariant unwraps in production code. Prefer `expect("why this is impossible")` or a local allow once the predicate runtime supports suppressions.
- `must_use_message_on_pub_result_option` is intentionally narrower than "always add bare `#[must_use]`": `Result` and `Option` already warn when ignored, and Clippy flags redundant bare attributes.
- `unsafe_requires_safety_comment` requires a direct `// SAFETY:` line before the unsafe block or impl. Wider module-level explanations may need to move closer to the operation.
- `no_blocking_io_in_async` catches obvious std blocking APIs only. It will not detect synchronous third-party calls hidden behind helper functions.
- `no_wildcard_imports_in_prod` is advisory because enum-variant globs and prelude imports can be reasonable in small scopes.
- Semantic predicates depend on the judge recognizing concrete changed spans. They should stay high-threshold and cite exact dependency or FFI changes before blocking.

## Fixtures

Each fixture in `fixtures/` contains one blocked or warned example and one allowed example for the corresponding predicate. The fixture shape matches the current harn-canon convention:

```json
{
  "predicate": "name",
  "cases": [
    {"expect": "Block", "files": [{"path": "src/lib.rs", "text": "..."}]},
    {"expect": "Allow", "files": [{"path": "src/lib.rs", "text": "..."}]}
  ]
}
```
