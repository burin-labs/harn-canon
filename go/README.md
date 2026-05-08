# Go Seed Predicate Pack

This pack covers Go modules, command packages, and reusable libraries. It targets high-signal review issues that changed source slices can catch cheaply: ignored errors, context propagation mistakes, library panics, overly broad exported APIs, lossy error wrapping, HTTP response leaks, weak randomness, goroutine lifetime leaks, and dependency vulnerability review.

## Stack Assumptions

- Go source files use `.go`; module metadata uses `go.mod` and `go.sum`.
- Production paths exclude `_test.go`, `test/`, `tests/`, and `testdata/` files.
- Generated Go files with the standard `// Code generated ... DO NOT EDIT.` marker are ignored by deterministic source predicates.
- Deterministic predicates use file-text scans until Harn Flow exposes a stable Go AST query API.
- Semantic predicates make one cheap judge call over changed Go/module files and use only evidence captured at authoring time.
- Advisory rules return `Warn` when idiomatic exceptions are common. Blocking rules are reserved for ignored errors, library panics, likely response-body leaks, security-sensitive randomness, goroutine leaks, and missing dependency-vulnerability evidence.

## Predicate Coverage

| Predicate | Mode | Verdict | Purpose |
|---|---|---|---|
| `no_ignored_errors` | deterministic | Block | Obvious blank-identifier discards of call results should not hide errors in production Go. |
| `context_first_arg` | deterministic | Warn | Exported APIs should place `context.Context` first unless an interface fixes the signature. |
| `no_panic_in_library` | deterministic | Block | Non-main library packages should return errors instead of panicking from normal failure paths. |
| `no_context_in_struct` | deterministic | Warn | Context values should be passed per call rather than stored in structs. |
| `no_empty_interface_in_api` | deterministic | Warn | Exported APIs should avoid `interface{}` and `any` when concrete types, type parameters, or small interfaces fit. |
| `wrap_errors_with_percent_w` | deterministic | Warn | Error context should preserve unwrap chains when callers may use `errors.Is` or `errors.As`. |
| `error_strings_not_capitalized` | deterministic | Warn | Error strings should compose cleanly when callers add context. |
| `http_response_body_closed` | deterministic | Block | Successful HTTP responses must have their bodies closed to release resources. |
| `no_math_rand_for_keys` | deterministic | Block | Security-sensitive keys, tokens, nonces, and secrets require `crypto/rand`, not `math/rand`. |
| `goroutine_leak_guard` | semantic | Block | Long-lived goroutines need credible cancellation, shutdown, or bounded-lifetime evidence. |
| `go_dependency_vulns_checked` | semantic | Block | Dependency changes should preserve or run govulncheck, Dependabot, OSV, or equivalent checks. |

## Evidence

Evidence scanned on 2026-05-08.

- Go docs and tutorials: Effective Go, Go error handling tutorial, Go 1.13 errors blog, package docs for `context`, `errors`, `fmt`, `io`, `net/http`, `crypto/rand`, and `math/rand`.
- Go Wiki: Code Review Comments for contexts, interfaces, panic guidance, crypto randomness, and error strings.
- Go Blog: pipeline cancellation patterns for goroutine shutdown.
- Staticcheck docs: correctness checks that include ignored-result and suspicious-code signals.
- Go vulnerability tooling and dependency docs: module dependency management and `govulncheck`.
- GitHub Dependabot docs: dependency update and security automation paths.

## Known False Positives

- Regex predicates do not parse Go. Comments, raw strings, nested function literals, unusual formatting, and aliases can confuse deterministic checks.
- `no_ignored_errors` intentionally catches obvious `_ = call()` and `value, _ := call()` shapes, but it cannot prove the discarded result has type `error`.
- `context_first_arg` and `no_empty_interface_in_api` are advisory because generated bindings and required interface signatures may force non-idiomatic signatures.
- `no_panic_in_library` ignores `package main` and tests, but it can still catch panics used for internal invariants. Prefer returning errors or documenting the public panic contract once suppressions exist.
- `http_response_body_closed` is conservative and file-scoped. It can miss helper-based close patterns or flag files that close through a different response variable.
- `no_math_rand_for_keys` is keyword-based. Non-security simulations with token-like names may need a local allow once the predicate runtime supports suppressions.
- Semantic predicates depend on the judge recognizing concrete changed spans. They should stay high-threshold and cite exact goroutine or dependency changes before blocking.

## Fixtures

Each fixture in `fixtures/` contains one blocked or warned example and one allowed example for the corresponding predicate. The fixture shape matches the current harn-canon convention:

```json
{
  "predicate": "name",
  "cases": [
    {"expect": "Block", "files": [{"path": "client.go", "text": "..."}]},
    {"expect": "Allow", "files": [{"path": "client.go", "text": "..."}]}
  ]
}
```
