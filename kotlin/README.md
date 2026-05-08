# Kotlin Seed Predicate Pack

This pack covers Kotlin JVM, Android, and Kotlin Multiplatform source with an emphasis on null-safety, coroutine structure, API clarity, and value-object idioms. The v0 rules favor simple source-text predicates for concrete failure modes and semantic predicates where platform types or async API design require code context.

## Stack Assumptions

- Files use `.kt` or `.kts` and target Kotlin 2.x-era language and coroutine practices.
- JVM and Android projects may use Gradle, kotlinx.coroutines, Jetpack lifecycle scopes, Compose, Java interop, detekt, and ktlint-style formatting.
- Deterministic predicates run over changed production Kotlin source text. Test, generated, Gradle build, and common platform test paths are excluded where appropriate.
- Semantic predicates use `ctx.semantic_judge(...)` and must cite concrete changed spans before blocking.
- The pack is a seed canon, not a replacement for the Kotlin compiler, explicit API mode, detekt, Android Lint, ktlint, or coroutine debug tooling.

## Predicate Coverage

| Predicate | Mode | Verdict | Purpose |
|---|---|---|---|
| `no_bang_bang` | deterministic | Block | Avoid production NPEs from non-null assertions. |
| `immutable_by_default` | deterministic | Warn | Prefer `val` over mutable `var` declarations. |
| `no_run_blocking_in_prod_path` | deterministic | Block | Keep blocking coroutine bridges out of production library code. |
| `no_global_scope_launch` | deterministic | Block | Require lifecycle-owned or caller-owned coroutine scopes. |
| `no_thread_sleep_in_suspend` | deterministic | Warn | Avoid blocking threads from suspending functions. |
| `blocking_io_uses_io_dispatcher` | deterministic | Warn | Keep obvious blocking IO off default or main coroutine dispatchers. |
| `explicit_visibility_for_top_level_api` | deterministic | Warn | Make top-level API visibility intentional. |
| `data_class_for_value` | deterministic | Warn | Prefer `data class` for simple value carriers. |
| `no_broad_detekt_suppressions` | deterministic | Warn | Keep static-analysis suppressions narrow and reviewable. |
| `no_platform_types_in_public_api` | semantic | Block | Normalize Java interop platform types before public exposure. |
| `suspend_for_async` | semantic | Block | Prefer suspend or Flow for new Kotlin async APIs. |
| `no_main_thread_blocking_work` | semantic | Block | Keep blocking work out of Android and UI main-thread paths. |

## Evidence

Evidence scanned on 2026-05-08.

- Kotlin documentation: null safety, type system, basic syntax, properties, visibility modifiers, coding conventions, data classes, coroutines basics, cancellation, and coroutine channels.
- Kotlin API guidelines: explicit API mode and public API simplicity.
- Android Developers: Kotlin coroutine usage and coroutine best practices for main-safety.
- Android Open Source Project API guidelines: asynchronous and non-blocking Kotlin API design.
- detekt documentation: style rules and suppression behavior used as ecosystem lint precedent.

## Known False Positives

- `no_bang_bang` is source-text based and can flag rare intentional assertions. Test paths are excluded, but production assertions should usually be replaced or localized with `requireNotNull`.
- `immutable_by_default` warns on any `var`, including stateful UI and persistence models where mutation is intentional.
- `no_run_blocking_in_prod_path` allows `Main.kt` and scripts as entry-point conventions, but other legitimate process entry filenames may need a suppression once suppressions exist.
- `blocking_io_uses_io_dispatcher` looks for common blocking APIs in coroutine bodies and may miss project-specific wrappers or flag code already confined by an injected dispatcher.
- `explicit_visibility_for_top_level_api` warns at source-text level and does not inspect Gradle explicit API mode.
- `data_class_for_value` catches only simple constructor-property classes with hand-rolled equality, and semantic review is still needed for identity-sensitive types.
- The semantic predicates depend on a cheap judge and should block only when the changed span clearly introduces the risk.

## Fixtures

Each fixture in `fixtures/` contains at least one blocked or warned production example and one allowed example for the corresponding predicate:

```json
{
  "predicate": "name",
  "cases": [
    {"expect": "Block", "files": [{"path": "src/main/kotlin/App.kt", "text": "..."}]},
    {"expect": "Allow", "files": [{"path": "src/main/kotlin/App.kt", "text": "..."}]}
  ]
}
```
