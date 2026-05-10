# Dart Seed Predicate Pack

This pack covers Dart application, package, and Flutter source with an emphasis on null safety, public-API hygiene, async correctness, and Flutter widget immutability. The v0 rules favor simple source-text predicates for concrete failure modes and semantic predicates where Dart and Flutter framework contracts require code context the regex layer cannot infer.

## Stack Assumptions

- Files use the `.dart` extension and target Dart 3.x (sound null safety required) and current Flutter stable.
- Projects may use the standard `pub` package layout (`lib/`, `bin/`, `test/`, `integration_test/`, `example/`) and code generation tools that emit `*.g.dart`, `*.freezed.dart`, `*.gr.dart`, `*.config.dart`, `*.mocks.dart`, `*.chopper.dart`, and protobuf `*.pb.dart` files.
- Deterministic predicates run over changed production Dart source text. Test, generated, and example paths are excluded from production-only rules.
- The `lib/`-only rules (`no_relative_lib_imports`, `effective_dart_documents_public_apis`) limit their scan to files inside a `lib/` segment so command-line entry points under `bin/` are not penalized.
- Semantic predicates use `ctx.semantic_judge(...)` and must cite concrete changed spans before blocking.
- The pack is a seed canon, not a replacement for `dart analyze`, `flutter analyze`, the official lint rule sets in `package:lints` or `package:flutter_lints`, or `dart format`.

## Predicate Coverage

| Predicate | Mode | Verdict | Purpose |
|---|---|---|---|
| `no_null_safety_opt_out` | deterministic | Block | Reject pre-null-safety `// @dart=2.x` markers in production code. |
| `no_force_null_assertion` | deterministic | Block | Avoid runtime crashes from postfix `!` null assertions. |
| `no_dynamic_in_signatures` | deterministic | Warn | Keep `dynamic` out of public function and method signatures. |
| `no_print_in_production` | deterministic | Warn | Production diagnostics should use `dart:developer`, `package:logging`, or the project logger. |
| `no_top_level_mutable_state` | deterministic | Warn | Top-level `var` is process-global mutable state and is rarely justified. |
| `no_broad_lint_ignores` | deterministic | Warn | `// ignore_for_file` directives should suppress one rule with a justification, not a bundle. |
| `prefer_const_constructor_for_widgets` | deterministic | Warn | Flutter Widget subclasses should declare a `const` constructor. |
| `no_relative_lib_imports` | deterministic | Warn | Library code under `lib/` should not climb out with `../` imports. |
| `widget_state_is_immutable` | semantic | Block | Stateless and inherited widgets must not hold mutable instance state. |
| `unawaited_futures_are_intentional` | semantic | Block | Discarded `Future`s inside async bodies must be awaited or marked `unawaited`. |
| `effective_dart_documents_public_apis` | semantic | Block | New public APIs in `lib/` need a `///` doc comment per Effective Dart. |

## Evidence

Evidence scanned on 2026-05-10.

- dart.dev language reference: null safety overview, language versioning markers, and the "understanding null safety" reference for the null assertion operator semantics.
- dart.dev linter rule docs: `avoid_print`, `avoid_dynamic_calls`, `prefer_final_fields`, `prefer_const_constructors_in_immutables`, `unawaited_futures`, `avoid_relative_lib_imports`, `public_member_api_docs`, and `null_check_on_nullable_type_parameter` as the canonical ecosystem lint precedent.
- dart.dev Effective Dart guides: usage and documentation pages for variable declaration style and public-API documentation rules.
- api.dart.dev: `dart:developer log()` and `dart:async unawaited()` reference pages.
- api.flutter.dev: `StatelessWidget` class docs and the `@immutable` annotation as the framework contract behind widget immutability.
- dart.dev tooling: pub package layout and the analyzer overview that govern import-path expectations and `// ignore_for_file` directives.

## Known False Positives

- `no_force_null_assertion` is source-text based. It can flag legitimate `expr!` uses where the type system genuinely cannot prove non-null (for example, a generated `late` field accessed after a documented init step). Until predicate-level suppressions exist, prefer narrowing the regex with a wrapper or refactoring the call site.
- `no_dynamic_in_signatures` warns on any function whose return or parameter type is the keyword `dynamic`. It does not currently detect `dynamic` inside generic positions like `List<dynamic>`, and it may catch generated adapters that legitimately return `dynamic`; route those files through `is_generated_path` or rename them to a generated suffix.
- `no_print_in_production` flags every `print` and `debugPrint` call. Flutter teams that intentionally use `debugPrint` behind `kDebugMode` may need a local suppression once one exists.
- `no_top_level_mutable_state` matches unindented `var` declarations and may miss `late var` declarations that span multiple lines; it can also flag intentionally-mutable test doubles that leak into production paths.
- `no_broad_lint_ignores` triggers when a single `// ignore_for_file` line lists three or more rules or when it disables a whole `type=` category. Single- or two-rule suppressions with a justification are allowed.
- `prefer_const_constructor_for_widgets` is file-scoped: it warns when a file declares a Widget subclass and contains no `const Capital(` declaration at two-space class-body indent. It can miss Widget subclasses that intentionally declare a `factory` constructor and it can over-allow files that mix const Widget classes with non-const ones — review the file as a whole when warned.
- `no_relative_lib_imports` flags only imports that begin with `../`. Same-directory `./sibling.dart` and `package:` imports are allowed.
- The semantic predicates depend on a cheap judge and should block only when the changed span clearly introduces the risk; rubrics list the carve-outs.

## Fixtures

Each fixture in `fixtures/` contains at least one blocked or warned production example and one allowed example for the corresponding predicate:

```json
{
  "predicate": "name",
  "cases": [
    {"expect": "Block", "files": [{"path": "lib/src/foo.dart", "text": "..."}]},
    {"expect": "Allow", "files": [{"path": "lib/src/foo.dart", "text": "..."}]}
  ]
}
```
