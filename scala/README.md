# Scala Seed Predicate Pack

This pack covers Scala 2.13 and Scala 3 source on the JVM, with an emphasis on null safety, immutability, total function shape, effect-system hygiene, and pattern-match exhaustiveness. The v0 rules favor simple source-text predicates for concrete failure modes and semantic predicates where effect-system boundaries or exhaustiveness require code context.

## Stack Assumptions

- Files use `.scala`. Worksheets (`.sc`) and sbt build files (`.sbt`) are out of scope; the v0 pack reads only compiled-source `.scala` files.
- Projects may use sbt, Mill, Bloop, Metals, ScalaTest, MUnit, ZIO, cats-effect, Akka, Pekko, or Spark; predicates target idioms that are common across these stacks rather than framework-specific patterns.
- Deterministic predicates run over changed production Scala source text. Test (`src/test/`, `src/it/`, `*Spec.scala`, `*Suite.scala`, `*Test(s).scala`, `*Properties.scala`), generated (`target/`, `.bloop/`, `.metals/`, `.bsp/`, `generated/`), and build script paths (`*.sbt`, `*.sc`) are excluded.
- Library-only predicates additionally exclude common entry-point filenames (`Main.scala`, `App.scala`, `Application.scala`, `Boot.scala`).
- Semantic predicates use `ctx.semantic_judge(...)` and must cite concrete changed spans before blocking.
- The pack is a seed canon, not a replacement for the Scala compiler, scalac `-Xfatal-warnings`, scalafix, scalafmt, or WartRemover.

## Predicate Coverage

| Predicate | Mode | Verdict | Purpose |
|---|---|---|---|
| `no_any_in_public_api` | deterministic | Warn | Avoid leaking `Any`/`AnyRef`/`AnyVal` in declared return types. |
| `no_null` | deterministic | Block | Use `Option`/`Either`/`Try` instead of `null` literals. |
| `immutable_by_default` | deterministic | Warn | Prefer `val` over mutable `var` declarations. |
| `no_return_keyword` | deterministic | Warn | Drop explicit `return`; nested non-local returns are deprecated since Scala 3.2. |
| `explicit_return_types_on_public_defs` | deterministic | Warn | Annotate public defs with explicit return types. |
| `no_get_on_option_or_try` | deterministic | Block | Avoid `.get` accessors that throw on absence/failure. |
| `no_unchecked_type_casts` | deterministic | Warn | Replace `asInstanceOf`/`isInstanceOf` with pattern matching. |
| `no_global_execution_context` | deterministic | Block | Take an `ExecutionContext` parameter instead of importing the global. |
| `no_await_in_library_code` | deterministic | Block | Keep `Await.result`/`Await.ready` at the process boundary. |
| `effect_typed_boundaries` | semantic | Block | Cross IO/ZIO ↔ Future only through documented adapters. |
| `no_unsafe_run_in_library_code` | semantic | Block | Run effects only in `IOApp`/`ZIOAppDefault`/Dispatcher boundaries. |
| `pattern_matches_are_exhaustive` | semantic | Warn | Match expressions need a sealed subject or explicit fallback. |

## Evidence

Evidence scanned on 2026-05-10.

- Scala 3 book and reference: functional error handling, vars/data types, methods, dropped non-local returns, and pattern matching with `TypeTest`.
- Scala 3 tour: pattern matching exhaustiveness on sealed types.
- Official Scala style guide: declarations, return-type guidance for public members.
- Scala overviews: futures, `Await`, and the global `ExecutionContext`.
- Cats Effect documentation: getting started and runtime escape hatches.
- ZIO documentation: the `ZIO[R, E, A]` effect type and runtime entry points.
- WartRemover wart catalogue: `Any`, `Null`, `Var`, `Return`, `OptionPartial`, `TryPartial`, `AsInstanceOf`, `IsInstanceOf` as ecosystem precedent.

## Known False Positives

- `no_any_in_public_api` matches return-type position only; `Any` in parameter types or as a generic upper bound (`[T <: Any]`) is not flagged. Method overloading on `Any` is occasionally intentional and the rule is Warn-level.
- `no_null` is source-text based and may flag the literal token inside string content (`"value is null"`). Test paths and Java-interop suppressions are out of scope; scope `null` to a local interop helper if you genuinely need it.
- `immutable_by_default` warns on every production `var`, including stateful UI, persistence, or buffer types where mutation is intentional.
- `no_return_keyword` matches statement-position `return` only and will miss inline early returns inside a single-line `if`/lambda.
- `explicit_return_types_on_public_defs` excludes only `private` defs; `protected`-scoped APIs are still flagged because they cross compilation-unit boundaries.
- `no_get_on_option_or_try` cannot disambiguate `Option.get` from a parameterless `def get` on a user-defined type, so it will flag the latter; rename or wrap such accessors.
- `no_unchecked_type_casts` warns on every cast, including legitimate Java-interop boundaries; suppress narrowly with a comment once suppressions exist.
- `no_global_execution_context` treats `Main.scala`/`App.scala`/`Application.scala`/`Boot.scala` as boundaries; other entry-point filenames may need a suppression.
- `no_await_in_library_code` accepts `Await` only in tests and recognized entry points; non-standard runner filenames will be flagged.
- The semantic predicates depend on a cheap judge and should block only when the changed span clearly introduces the risk.

## Fixtures

Each fixture in `fixtures/` contains at least one blocked or warned production example and one allowed example for the corresponding predicate:

```json
{
  "predicate": "name",
  "cases": [
    {"expect": "Block", "files": [{"path": "src/main/scala/App.scala", "text": "..."}]},
    {"expect": "Allow", "files": [{"path": "src/main/scala/App.scala", "text": "..."}]}
  ]
}
```
