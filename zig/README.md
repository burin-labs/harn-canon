# Zig Seed Predicate Pack

This pack covers Zig source (`.zig`) and the `build.zig.zon` package manifest. Zig is a young, rapidly evolving language; v0 focuses on the highest-signal review issues that survive across the recent stable releases and current 0.16 toolchains: silent error-handling shortcuts, stale standard-library API shapes, unjustified unsafe casts, `@panic` in library paths, test-time leak detection, and supply-chain hygiene in the package manifest.

## Stack assumptions

- Source predicates target Zig 0.15.x and 0.16.x. Older releases predate `build.zig.zon` and the modern cast/error/container APIs; the predicates here are not expected to be useful below 0.12.
- Production paths exclude `_test.zig` and `test_*.zig` files plus `tests/`, `test/`, `testdata/`, `examples/`, and `example/` directories. Test-block heuristics rely on the convention that test declarations appear at the top level of a file.
- `build.zig.zon` predicates filter on the literal filename. Generated lock files and vendored caches are not in scope for v0.
- Deterministic predicates operate on changed source text. Zig has no published stable AST query API yet, so regex-based matching is intentionally conservative — the pack errs toward false negatives rather than false positives.
- Semantic predicates are reserved for issues that cannot be reliably expressed as syntactic checks. They block only when the judge can cite a concrete changed span.

## Predicate coverage

| Predicate | Mode | Verdict | Purpose |
|---|---|---|---|
| `no_silent_error_swallow` | deterministic | Block | Empty `catch {}` and `catch \|_\| {}` discard error unions and must be replaced with explicit handling. |
| `no_catch_unreachable_in_prod` | deterministic | Warn | `catch unreachable` outside test files asserts the call cannot fail without justification. |
| `unsafe_cast_has_justification` | deterministic | Warn | `@truncate`, `@ptrCast`, `@alignCast`, `@bitCast`, and `@intCast` should carry an inline `//` comment explaining the soundness argument. |
| `no_panic_in_production` | deterministic | Warn | `@panic(...)` calls in non-test source crash the program; libraries should return errors instead. |
| `tests_use_testing_allocator` | deterministic | Warn | Test files that allocate via `page_allocator` or `c_allocator` skip leak detection; default to `std.testing.allocator`. |
| `build_zon_min_zig_version_set` | deterministic | Warn | `build.zig.zon` should set `.minimum_zig_version` so toolchain assumptions stay machine-readable. |
| `build_zon_dependency_hash_pinned` | deterministic | Block | URL-based dependency entries in `build.zig.zon` must declare a `.hash` so package fetches are content-verified. |
| `no_std_json_parser_api` | deterministic | Block | Current Zig code should use `std.json.parseFromSlice` or `std.json.Scanner`, not the removed `std.json.Parser` type. |
| `parsed_json_arrayhashmap_has_single_owner` | deterministic | Block | `std.json.ArrayHashMap` ownership stays single-owner: parsed values deinit through `parsed.deinit()`, duplicated stored keys are freed, and unused duplicated `getOrPut` keys are freed on `found_existing`. |
| `hashmap_count_uses_count_method` | deterministic | Block | Zig hash maps expose their element count through `.count()`; stale `.size` reads should not ship. |
| `enum_tags_use_tag_name_builtin` | deterministic | Block | Enum and tagged-union values use the `@tagName(value)` builtin for names, not stale `std.meta.tagToString(...)` calls. |
| `arraylist_uses_unmanaged_api` | deterministic | Block | Current `std.ArrayList(T)` values initialize with `.empty`; allocator-bearing calls happen on methods. |
| `defer_block_closes_without_semicolon` | deterministic | Block | `defer { ... }` closes with `}` only; `};` after the block is a syntax error. |
| `doc_comments_attach_to_declarations` | deterministic | Block | `///` doc comments attach to declarations and fields; implementation notes before statements should use `//`. |
| `assertion_on_ungrounded_output` | deterministic | Block | A changed test that asserts an author literal against the output of an in-repo producing symbol (serialize/format/encode/parse/write family) whose value was never observed this session (`ctx.observed_symbols`) must observe-then-assert instead of asserting a hand-simulated value. |
| `allocator_lifetime_hygiene` | semantic | Block | Heap allocations need a matching `defer`/`errdefer` free or a documented ownership transfer. |
| `no_hardcoded_secrets` | semantic | Block | Credentials, tokens, and private keys must not be embedded as string literals in Zig source. |
| `integer_endianness_explicit` | semantic | Warn | Multi-byte integer I/O across a serialization boundary should name the endianness rather than relying on host byte order. |

## Evidence

Evidence scanned on 2026-05-10, 2026-06-23, 2026-07-01, 2026-07-02, and 2026-07-03.

- Zig language reference (master) for `@truncate`, `@ptrCast`, `@alignCast`, `@bitCast`, `@intCast`, `@panic`, `unreachable`, error sets, `errdefer`, `Choosing-an-Allocator`, `Memory`, `byteSwap`, and the build system overview.
- Zig standard library docs for `std.testing.allocator`, `std.mem.readInt`, `std.mem.writeInt`.
- Zig source `doc/build.zig.zon.md` for the manifest schema, including `.minimum_zig_version` (advisory) and the `.hash` requirement on URL-based dependencies.
- Zig Build System tutorial (`ziglang.org/learn/build-system`) for package-manager workflow guidance.
- The Zig Guide community handbook (`zig.guide`) for error-handling and allocator idioms.
- Zig 0.16.0 release notes for the migration to unmanaged containers and allocator-taking ArrayList methods.
- Zig standard library JSON source and current zig.guide JSON examples for `std.json.parseFromSlice`.
- Zig standard library JSON parser, JSON hashmap, array-hash-map sources, and memory docs for `std.json.ArrayHashMap` ownership, cleanup, and `getOrPut` key lifetime.
- Zig standard library hash map and array hash map sources, plus current zig.guide hash map examples, for the public `.count()` API on map values.
- Zig language reference, Zig standard library `std.meta` source, and current zig.guide enum examples for `@tagName(value)` and `std.meta.stringToEnum`.
- Zig language reference and zig.guide examples for `defer` semantics and block-form usage.
- Zig language reference and zig.guide documentation-generation examples for doc-comment attachment sites.
- OWASP Secrets Management and Software Supply Chain Security cheat sheets, plus GitHub secret-scanning documentation, for the secret-handling and dependency-hash predicates.
- Zig testing docs (`Zig-Test`, `std.testing.expectEqualStrings`) and the zig.guide test chapter for the assertion node kinds the observe-before-assert detector reasons over.

## Known false positives and negatives

- Regex predicates do not parse Zig. Casts, `catch unreachable`, and `@panic` calls inside string literals or comments will trigger the deterministic predicates. Adding the comment-based escape valve documented in each predicate (or moving the literal out of the changed region) silences these.
- `no_silent_error_swallow` only flags syntactically empty bodies. `catch {} // intentional` is treated as the author having opted into the swallow with a documented reason and is not blocked.
- `no_catch_unreachable_in_prod` filters by path. A `catch unreachable` inside a `test "..."` block in a non-`_test.zig` file is still flagged. Move the test to a `_test.zig` file or add explicit error handling.
- `unsafe_cast_has_justification` requires the justification on the same line as the cast. Long explanations on the preceding line currently trip the warning; either inline a short justification or rewrite the cast to avoid the builtin.
- `no_panic_in_production` does not distinguish CLI `main()` from library code. Top-level binaries that legitimately panic on unrecoverable startup failures should suppress the warning per call site.
- `tests_use_testing_allocator` keys on the literal identifiers `page_allocator` and `c_allocator`. Aliased re-exports (`const A = std.heap.page_allocator;` re-exported under another name) will be missed.
- `build_zon_dependency_hash_pinned` only flags URL-based entries that lack a hash; entries using `.path = ...` are skipped, matching the manifest schema.
- `no_std_json_parser_api` is a token scan. A prose comment or string literal mentioning `std.json.Parser` will be blocked until the pack can use AST facts.
- `parsed_json_arrayhashmap_has_single_owner` has file-local checks. The parsed-value check requires `std.json.ArrayHashMap`, `std.json.parseFromSlice`, and a manual `.value...map.deinit(...)` in the same changed file. The manual-key check looks for `allocator.dupe` or `dupeZ`, insertion through common `.map` insert APIs, and `.map.deinit(...)` without an entry loop that frees `entry.key_ptr.*` or `entry.key`. The `getOrPut` collision check requires a duplicated `u8` key, `getOrPut`, and a `found_existing` branch, then expects a direct `free(key)`-shaped cleanup for the unused duplicate. It can miss helper-based cleanup in another file and can block unusual code that intentionally copies a parsed value into a new owner or uses a custom key-cleanup helper.
- `hashmap_count_uses_count_method` requires a recognized Zig hash map type in the file and then scans for likely map-shaped `.size` reads such as `map.size`, `user_map.size`, or `.items.map.size`. It can miss unusually named map variables and can false-positive on a non-map field named `size` in the same changed file.
- `enum_tags_use_tag_name_builtin` is an exact token scan. A comment or string literal that mentions `std.meta.tagToString(` will be blocked until the pack can use AST facts.
- `arraylist_uses_unmanaged_api` blocks `std.ArrayList(T).init(allocator)` in current Zig code and recognizes
  direct `const` or `var` declarations of `std.ArrayList(T) = .empty` whose mutating or ownership calls still
  omit allocator arguments. Projects pinned to older Zig releases may need to suppress or opt out of this predicate.
  The method-call arm can miss aliases and helper-returned lists, and can block unrelated allocator-less method
  calls in the same file as a direct `.empty` declaration.
- `defer_block_closes_without_semicolon` scans from a `defer {` opener to a line containing only `};`. A multiline struct literal inside a defer body that also has a standalone `};` line can false-positive.
- `doc_comments_attach_to_declarations` is intentionally narrow. It blocks `///` immediately before statement-shaped lines such as `return`, `try`, `defer`, and `if`, but can miss misplaced doc comments before local `const` or `var` declarations to avoid false-positives on documented top-level declarations.
- `assertion_on_ungrounded_output` is the observe-before-assert grounding detector. It parses the changed test file with the bundled Zig tree-sitter grammar (`std/ast`), maps `const x = <producer(...)>` bindings whose callee role is in the producing family (serialize/format/encode/parse/write/etc.), then blocks an assertion callee (`expect`/`expectEqual*`/`expectStringStartsWith`/…) that carries an author string literal and references a producer-bound variable **when the producing callee is absent from `ctx.observed_symbols`**. The discriminator is provenance, not shape: the identical assertion is allowed once an `observe_output` probe has recorded the producing symbol in `ctx.observed_symbols`, so a run that already grounded is never fought. It keys on the same-file `output = producer(...)` binding, so an assertion on a producer output flowing through a helper in another file is missed. It runs on files the shared `is_test_zig_path` helper recognizes as tests: `_test.zig`, `test_*.zig`, and `tests/`, `test/`, `testdata/`, `examples/`, or `example/` directory segments at any depth. `ctx.observed_symbols` is host-injected (Burin threads it from the agent event stream in follow-on work); with no host it defaults to empty, so the detector treats every producer as unobserved.
- Semantic predicates depend on a cheap judge. They should stay high-threshold and cite concrete changed spans before blocking.

## Design notes

- `const_by_default` is omitted: the Zig compiler already emits a hard error on `var` declarations that are never reassigned. A predicate would be redundant with the toolchain.
- `error_union_propagation` is partly handled by the compiler, which rejects discarded fallible results outside an explicit `_ = ...` slot. The remaining hand-rolled escapes, `catch {}` and `catch unreachable`, are covered by `no_silent_error_swallow` and `no_catch_unreachable_in_prod`.
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
