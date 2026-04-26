# Swift Seed Predicate Pack

This pack covers Swift application and package code with an emphasis on crash prevention, UI responsiveness, ARC memory safety, and Swift 6 data-race safety. The v0 rules deliberately prefer simple source-text predicates where a failure mode is concrete, and semantic predicates where Swift syntax and framework lifetime rules are too contextual for regex alone.

## Stack Assumptions

- Files use the `.swift` extension and target Swift 5.10 through Swift 6.x.
- Apple-platform code may use SwiftUI, UIKit, AppKit, Combine, Swift Testing, XCTest, Dispatch, and OSLog.
- Deterministic predicates run over changed production Swift source text. `Tests`, `TestSupport`, and preview files are excluded from production-only rules.
- Semantic predicates use `ctx.semantic_judge(...)` and must cite concrete changed spans before blocking.
- The pack is a seed canon, not a replacement for SwiftSyntax, SwiftLint, the Swift compiler, Xcode diagnostics, or runtime profiling.

## Predicate Coverage

| Predicate | Mode | Verdict | Purpose |
|---|---|---|---|
| `no_force_unwrap` | deterministic | Block | Avoid production crashes from force-unwrapping optionals. |
| `no_force_try` | deterministic | Block | Avoid runtime traps from `try!`. |
| `no_force_cast` | deterministic | Block | Avoid runtime traps from `as!`. |
| `no_dispatch_main_sync` | deterministic | Block | Prevent main-queue deadlocks and UI hangs. |
| `prefer_structured_concurrency` | deterministic | Warn | Prefer Swift concurrency primitives over new low-level queue/thread work. |
| `main_actor_on_ui_observable_state` | deterministic | Warn | UI-bound observable state should declare main-actor isolation. |
| `unchecked_sendable_requires_rationale` | deterministic | Warn | `@unchecked Sendable` requires a local synchronization rationale. |
| `no_top_level_mutable_state` | deterministic | Warn | Top-level mutable state is risky under Swift 6 concurrency. |
| `no_print_in_production` | deterministic | Warn | Production diagnostics should use OSLog or project logging. |
| `no_retain_cycle_in_escaping_closure` | semantic | Block | Escaping closures that capture `self` must avoid retain cycles. |
| `ui_state_mutations_stay_main_actor` | semantic | Block | UI and observable state mutations must stay main-actor isolated. |
| `sendable_cross_actor_boundaries_are_safe` | semantic | Block | Mutable non-Sendable state must not cross concurrency domains unsafely. |

## Evidence

Evidence scanned on 2026-04-26.

- Swift book: optional chaining vs forced unwrapping, error handling, type casting, concurrency, Sendable, constants and variables, and ARC closure capture lists.
- Swift.org: Swift 6 announcement and package ecosystem guidance for compile-time data-race safety.
- Apple Developer Documentation: app responsiveness, DispatchQueue behavior, Sendable, and unified logging with `Logger`.
- SwiftLint rule docs: `force_unwrapping`, `force_try`, `force_cast`, and `implicitly_unwrapped_optional` behavior as widely adopted ecosystem lint precedent.
- Swift Forums: current discussion on accidental retain cycles from strong closure captures.

## Known False Positives

- `no_force_unwrap` is source-text based and can flag rare intentional force unwraps or implicitly unwrapped optional declarations outside recognized test/preview paths; it may miss unwraps at the end of a line until SwiftSyntax-backed matching exists.
- `prefer_structured_concurrency` warns on any new Dispatch, OperationQueue, Thread, or pthread usage, including legitimate low-level adapters.
- `main_actor_on_ui_observable_state` warns at file granularity when a UI-facing file has observable state but no `@MainActor`; helper-only files may need a local suppression once suppressions exist.
- `no_top_level_mutable_state` treats unindented `var` declarations as top-level state; generated code should be excluded by repository policy.
- The semantic predicates depend on a cheap judge and should block only when the changed span clearly introduces the risk.

## Fixtures

Each fixture in `fixtures/` contains at least one blocked or warned production example and one allowed example for the corresponding predicate:

```json
{
  "predicate": "name",
  "cases": [
    {"expect": "Block", "files": [{"path": "Sources/App/File.swift", "text": "..."}]},
    {"expect": "Allow", "files": [{"path": "Sources/App/File.swift", "text": "..."}]}
  ]
}
```
