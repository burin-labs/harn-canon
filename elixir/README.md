# Elixir Seed Predicate Pack

This pack covers general-purpose Elixir application and library code on top of the BEAM. It targets review-slice issues with clear correctness, debuggability, or convention impact: stray debug helpers committed by accident, unbounded atom creation that can exhaust the BEAM atom table, idiomatic flow-control choices, predicate naming, exception handling that drops stacktraces, pipeline readability, error contract drift, GenServer state-shape leakage, and case/cond bodies that should be function clauses.

## Stack Assumptions

- Source files use the `.ex` and `.exs` extensions.
- Production paths exclude any path under `test/`, `tests/`, `_build/`, `deps/`, `cover/`, or `.elixir_ls/`, and any file ending in `_test.exs`.
- Projects target modern Elixir (1.14+) with `dbg/1`, the standard `Logger` API, `String.to_existing_atom/1`, and `reraise/2` available.
- Deterministic predicates run over changed source text until Flow exposes a stable Elixir AST query API. Rules with meaningful false-positive risk warn rather than block.
- Semantic predicates make a single judge call over changed Elixir files and stay conservative — they should only fire when they can cite concrete changed spans.

## Predicate Coverage

| Predicate | Mode | Verdict | Purpose |
|---|---|---|---|
| `no_io_inspect` | deterministic | Block | `IO.inspect` is debug instrumentation, not production logging; it leaks state and burns IO. |
| `no_dbg_macro` | deterministic | Block | `dbg/0` and `dbg/1` are interactive-debug helpers and should not appear in shipped code. |
| `no_iex_pry` | deterministic | Block | `IEx.pry/0` breakpoints only work in an attached IEx shell and stall production processes. |
| `no_unsafe_to_atom` | deterministic | Block | `String.to_atom/1`, `List.to_atom/1`, and the `:erlang` equivalents create unbounded atoms that the BEAM never garbage-collects. |
| `unless_with_else` | deterministic | Warn | `unless ... else` inverts reader expectations; flip the condition and use `if`. |
| `predicate_function_naming` | deterministic | Warn | Predicate functions should end in `?` and not also start with `is_`; the `is_` prefix is reserved for guard-safe macros. |
| `no_raise_inside_rescue` | deterministic | Block | Raising a fresh exception inside `rescue` discards the original stacktrace; use `reraise` to preserve it. |
| `pipe_chain_readability` | deterministic | Warn | Long pipelines without intermediate bindings hide intent and make stack traces harder to read. |
| `tagged_error_tuples` | semantic | Block | Public APIs should return `{:ok, value}` / `{:error, reason}` tuples or a bang variant, not bare atoms or `nil`. |
| `genserver_callback_boundary` | semantic | Block | GenServer callbacks should not leak fresh internal state shapes or raw implementation types across the process boundary. |
| `pattern_match_over_conditional` | semantic | Warn | Function bodies that are a single `case` or `cond` over the function's own arguments should be split into function-head clauses. |

## Evidence

Evidence scanned on 2026-05-10.

- Elixir official documentation (HexDocs `main`): code anti-patterns, process anti-patterns, naming conventions, library guidelines, the `IO`, `Kernel`, `String`, `IEx`, `Process`, and `GenServer` modules, and the case/cond/if guide.
- Credo static analysis checks: `Warning.IoInspect`, `Warning.Dbg`, `Warning.IExPry`, `Warning.UnsafeToAtom`, `Warning.RaiseInsideRescue`, `Refactor.UnlessWithElse`, `Refactor.PipeChainStart`, `Refactor.Nesting`, `Readability.PredicateFunctionNames`.

## Known False Positives

- Regex predicates are source-text checks. Comments, heredocs, string literals, and metaprogramming can fool them until AST-backed matching lands.
- `no_io_inspect`, `no_dbg_macro`, and `no_iex_pry` may flag intentional production diagnostics. Prefer `Logger` with explicit levels; suppress narrowly once the runtime supports it.
- `no_dbg_macro` matches `dbg(` after a non-word, non-dot, non-colon character. A local variable accidentally named `dbg` will trip the regex; rename the binding.
- `no_unsafe_to_atom` blocks every callsite, including ones whose input is statically known. The recommended replacement is an explicit map lookup or `String.to_existing_atom/1`.
- `unless_with_else` looks for an `else` within ~400 characters of the matching `unless ... do`, which is conservative for long branches; split very large branches before relying on the linter.
- `predicate_function_naming` flags `defmacro is_foo?` even though the `is_` prefix is correct for guard-safe macros — the trailing `?` is what makes the name violate the convention. Rename to `is_foo` (no trailing `?`) for guard macros.
- `no_raise_inside_rescue` matches `raise <Identifier>` within ~20 lines of a `rescue` clause and does not catch every layout. It also does not detect re-raising via `Kernel.reraise/2`, which is the intended replacement.
- `pipe_chain_readability` counts contiguous lines that begin with `|>`. A chain split across `|>` and inline calls on the same line, or a chain that interleaves comments, can read as shorter than it is.
- Semantic predicates depend on a cheap judge and should stay high-threshold until Flow exposes a structured Elixir AST and behaviour-aware data flow.

## Fixtures

Each fixture in `fixtures/` contains one blocked or warned example and one allowed example for the corresponding predicate. The fixture shape mirrors the existing seed packs:

```json
{
  "predicate": "name",
  "cases": [
    {"expect": "Block", "files": [{"path": "lib/my_app/service.ex", "text": "..."}]},
    {"expect": "Allow", "files": [{"path": "lib/my_app/service.ex", "text": "..."}]}
  ]
}
```
