# Zig Seed Predicate Pack

This pack covers Zig source (`.zig`) and the `build.zig.zon` package manifest. Zig is a young, rapidly evolving language; v0 focuses on the highest-signal review issues that survive across the recent stable releases (0.13.x and 0.14.x): silent error-handling shortcuts, unjustified unsafe casts, `@panic` in library paths, test-time leak detection, and supply-chain hygiene in the package manifest.

## Stack Assumptions

- Source predicates target Zig 0.13.x and 0.14.x. Older releases predate `build.zig.zon` and the modern cast/error builtins; the predicates here are not expected to be useful below 0.12.
- Production paths exclude `_test.zig` and `test_*.zig` files plus `tests/`, `test/`, `testdata/`, `examples/`, and `example/` directories. Test-block heuristics rely on the convention that test declarations appear at the top level of a file.
- `build.zig.zon` predicates filter on the literal filename. Generated lock files and vendored caches are not in scope for v0.
- Deterministic predicates operate on changed source text. Zig has no published stable AST query API yet, so regex-based matching is intentionally conservative — the pack errs toward false negatives rather than false positives.
- Semantic predicates are reserved for issues that cannot be reliably expressed as syntactic checks. They block only when the judge can cite a concrete changed span.

## Predicate Coverage

| Predicate | Mode | Verdict | Purpose |
|---|---|---|---|
| `no_silent_error_swallow` | deterministic | Block | Empty `catch {}` and `catch \|_\| {}` discard error unions and must be replaced with explicit handling. |
| `no_catch_unreachable_in_prod` | deterministic | Warn | `catch unreachable` outside test files asserts the call cannot fail without justification. |
| `unsafe_cast_has_justification` | deterministic | Warn | `@truncate`, `@ptrCast`, `@alignCast`, `@bitCast`, and `@intCast` should carry an inline `//` comment explaining the soundness argument. |
| `no_panic_in_production` | deterministic | Warn | `@panic(...)` calls in non-test source crash the program; libraries should return errors instead. |
| `tests_use_testing_allocator` | deterministic | Warn | Test files that allocate via `page_allocator` or `c_allocator` skip leak detection; default to `std.testing.allocator`. |
| `build_zon_min_zig_version_set` | deterministic | Warn | `build.zig.zon` should set `.minimum_zig_version` so toolchain assumptions stay machine-readable. |
| `build_zon_dependency_hash_pinned` | deterministic | Block | URL-based dependency entries in `build.zig.zon` must declare a `.hash` so package fetches are content-verified. |
| `allocator_lifetime_hygiene` | semantic | Block | Heap allocations need a matching `defer`/`errdefer` free or a documented ownership transfer. |
| `no_hardcoded_secrets` | semantic | Block | Credentials, tokens, and private keys must not be embedded as string literals in Zig source. |
| `integer_endianness_explicit` | semantic | Warn | Multi-byte integer I/O across a serialization boundary should name the endianness rather than relying on host byte order. |

## Evidence

Evidence scanned on 2026-05-10.

- Zig language reference (master) for `@truncate`, `@ptrCast`, `@alignCast`, `@bitCast`, `@intCast`, `@panic`, `unreachable`, error sets, `errdefer`, `Choosing-an-Allocator`, `Memory`, `byteSwap`, and the build system overview.
- Zig standard library docs for `std.testing.allocator`, `std.mem.readInt`, `std.mem.writeInt`.
- Zig source `doc/build.zig.zon.md` for the manifest schema, including `.minimum_zig_version` (advisory) and the `.hash` requirement on URL-based dependencies.
- Zig Build System tutorial (`ziglang.org/learn/build-system`) for package-manager workflow guidance.
- The Zig Guide community handbook (`zig.guide`) for error-handling and allocator idioms.
- OWASP Secrets Management and Software Supply Chain Security cheat sheets, plus GitHub secret-scanning documentation, for the secret-handling and dependency-hash predicates.

## Known False Positives and Negatives

- Regex predicates do not parse Zig. Casts, `catch unreachable`, and `@panic` calls inside string literals or comments will trigger the deterministic predicates. Adding the comment-based escape valve documented in each predicate (or moving the literal out of the changed region) silences these.
- `no_silent_error_swallow` only flags syntactically empty bodies. `catch {} // intentional` is treated as the author having opted into the swallow with a documented reason and is not blocked.
- `no_catch_unreachable_in_prod` filters by path. A `catch unreachable` inside a `test "..."` block in a non-`_test.zig` file is still flagged. Move the test to a `_test.zig` file or add explicit error handling.
- `unsafe_cast_has_justification` requires the justification on the same line as the cast. Long explanations on the preceding line currently trip the warning; either inline a short justification or rewrite the cast to avoid the builtin.
- `no_panic_in_production` does not distinguish CLI `main()` from library code. Top-level binaries that legitimately panic on unrecoverable startup failures should suppress the warning per call site.
- `tests_use_testing_allocator` keys on the literal identifiers `page_allocator` and `c_allocator`. Aliased re-exports (`const A = std.heap.page_allocator;` re-exported under another name) will be missed.
- `build_zon_dependency_hash_pinned` only flags URL-based entries that lack a hash; entries using `.path = ...` are skipped, matching the manifest schema.
- Semantic predicates depend on a cheap judge. They should stay high-threshold and cite concrete changed spans before blocking.

## Design Notes

- `const_by_default` is omitted: the Zig compiler already emits a hard error on `var` declarations that are never reassigned. A predicate would be redundant with the toolchain.
- `error_union_propagation` as written in the parent issue is partly handled by the compiler (which rejects calls to fallible functions whose result is discarded outside an explicit `_ = ...` slot). The remaining hand-rolled escape — `catch {}` and `catch unreachable` — is covered by `no_silent_error_swallow` and `no_catch_unreachable_in_prod`.
- `build.zig.zon` predicates intentionally use `.hash`-presence as a supply-chain proxy. The Zig package manager uses the hash as the source of truth, so a missing hash is a security issue, not a style nit.

## Fixtures

Each fixture in `fixtures/` contains at least one blocked or warned example and one allowed example for the corresponding predicate. The fixture shape matches the current harn-canon convention:

```json
{
  "predicate": "name",
  "cases": [
    {"name": "case_name", "expect": "Block", "files": [{"path": "src/x.zig", "text": "..."}]},
    {"name": "case_name", "expect": "Allow", "files": [{"path": "src/x.zig", "text": "..."}]}
  ]
}
```
