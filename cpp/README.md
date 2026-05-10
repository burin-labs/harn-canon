# C++ Seed Predicate Pack

This pack covers plain C++ application and library code with an emphasis on memory safety, modern initialization, header hygiene, and special-member discipline. The v0 rules deliberately use simple source-text predicates where a failure mode is concrete (raw `new`/`delete`, `malloc`/`free`, `NULL`, missing include guards, `using namespace` in headers, C-style casts, `typedef`) and lean on semantic predicates where C++ class context is too rich for regex alone (Rule of Five, member initialization, const correctness).

## Stack Assumptions

- C++ source files use `.cpp`, `.cxx`, `.cc`, or `.c++`. Headers use `.h`, `.hpp`, `.hh`, `.hxx`, `.h++`, `.ipp`, `.tpp`, or `.inl`.
- The pack targets C++17 and later. `nullptr`, `=default`/`=delete`, in-class member initializers, `using` aliases, and named casts are all assumed available.
- Production paths exclude any path under `test/`, `tests/`, `Test/`, `Tests/`, `unittest/`, `unittests/`, `gtest/`, `example/`, `examples/`, `sample/`, `samples/`, `bench/`, `benchmark/`, `benchmarks/`, `demo/`, `demos/`, `fuzz/`, `third_party/`, `thirdparty/`, `vendor/`, `external/`, `extern/`, `deps/`, `build/`, `_build/`, `cmake-build*`, or `.deps/`. Files matching `*_test.{cpp,cc,cxx}` and `*Test.{cpp,cc}` are also excluded.
- Header-scoped predicates (`header_include_guard_or_pragma_once`, `no_using_namespace_in_header`) inspect every changed header outside `third_party/` and similar vendor paths.
- Deterministic predicates run over changed source text until Flow exposes a stable Clang/`libclang` AST query API; semantic predicates make a single judge call over the changed slice.
- The pack is a seed canon, not a replacement for clang-tidy, the C++ compiler, AddressSanitizer/UBSan, or runtime profiling.

## Predicate Coverage

| Predicate | Mode | Verdict | Purpose |
|---|---|---|---|
| `no_raw_new_delete` | deterministic | Block | Production C++ should not call `new` or `delete` directly; use `std::make_unique`, `std::make_shared`, or a stack/`std::vector` allocation. |
| `no_naked_malloc_free` | deterministic | Block | Production C++ should not call C allocators; use RAII containers and smart pointers. |
| `prefer_nullptr_over_null` | deterministic | Warn | Pointer constants should be `nullptr`; `NULL` is an integer macro that breaks overload resolution. |
| `header_include_guard_or_pragma_once` | deterministic | Block | Every C++ header needs `#pragma once` or an `#ifndef`/`#define`/`#endif` guard. |
| `no_using_namespace_in_header` | deterministic | Block | Headers must not import a namespace at global scope; doing so leaks symbols into every translation unit that includes them. |
| `no_c_style_cast_in_prod` | deterministic | Warn | C-style primitive casts hide intent; prefer `static_cast`, `const_cast`, `reinterpret_cast`, or `dynamic_cast`. |
| `prefer_using_over_typedef` | deterministic | Warn | Use `using` aliases; they read left-to-right and support template aliases that `typedef` cannot express. |
| `rule_of_five_consistency` | semantic | Block | Classes that declare any of dtor/copy/move special members must declare or `=default`/`=delete` the remaining set. |
| `members_initialized` | semantic | Block | Class data members of fundamental, pointer, or enum type must be initialized either in-class or in every constructor. |
| `const_correctness_on_pub_api` | semantic | Warn | Public or protected member functions that do not modify `*this` should be declared `const`. |

## Evidence

Evidence scanned on 2026-05-10.

- ISO C++ Core Guidelines: R.10, R.11, ES.47, ES.49, SF.7, SF.8, T.43, C.21, C.48, Type.6, and Con.2.
- LLVM clang-tidy checks: `cppcoreguidelines-owning-memory`, `cppcoreguidelines-no-malloc`, `cppcoreguidelines-pro-type-cstyle-cast`, `cppcoreguidelines-pro-type-member-init`, `cppcoreguidelines-special-member-functions`, `modernize-use-nullptr`, `modernize-use-using`, `llvm-header-guard`, `google-readability-casting`, and `readability-make-member-function-const`.
- cppreference: `nullptr`, `unique_ptr`, the rule of three/five, and the `#include` and `#pragma once` preprocessor reference pages.
- Google C++ Style Guide: namespaces section on `using namespace` discipline.

## Known False Positives

- All deterministic predicates scan raw file text. Source comments, raw string literals, and `#define` bodies that contain `new`, `delete`, `malloc`, `NULL`, `typedef`, or `using namespace` token sequences will be flagged until the pack runs against an AST query layer.
- `no_raw_new_delete` matches `new T` and `delete ptr` in any context. Placement `new` (`new (mem) T`) deliberately bypasses the regex (`new` is followed by `(`, not an identifier); flag-and-grep is the recommended audit until placement new gets first-class detection.
- `no_naked_malloc_free` matches the bare `malloc(`, `calloc(`, `realloc(`, and `free(` token sequences. Member methods or namespace-scoped helpers named `free` (e.g., `pool.free()`, `arena::free()`) will also match; suppress locally once predicate suppressions land.
- `prefer_nullptr_over_null` flags `NULL` only when it is on the right-hand side of an assignment, comparison, return, function argument, ternary, or compared in Yoda style. `#define NULL 0` and `#undef NULL` lines escape detection by virtue of not matching the operator-prefix pattern.
- `header_include_guard_or_pragma_once` accepts any pair of `#ifndef`/`#define` tokens in the file. A header that uses `#ifndef`/`#define` for a feature flag but lacks a real guard will be allowed; a real header guard is the dominant pattern in practice.
- `no_using_namespace_in_header` flags `using namespace` even inside templates, function bodies, or anonymous namespaces inside the header. Function-local `using namespace` is acceptable C++ but is intentionally discouraged at this layer to keep the rule simple.
- `no_c_style_cast_in_prod` is conservative: it only matches casts to fundamental types, fixed-width integers, and the standard character/`void` types. C-style casts to user-defined types are not flagged here; clang-tidy's `cppcoreguidelines-pro-type-cstyle-cast` covers the broader case.
- `prefer_using_over_typedef` flags every `typedef` line, including those inside `extern "C"` blocks bridging to a C API. Suppress locally once predicate suppressions land.
- The semantic predicates (`rule_of_five_consistency`, `members_initialized`, `const_correctness_on_pub_api`) depend on a cheap judge and should block (or warn) only when the changed span clearly introduces the risk; the rubrics call out the common exceptions.

## Fixtures

Each fixture in `fixtures/` contains at least one blocked or warned production example and one allowed example for the corresponding predicate:

```json
{
  "predicate": "name",
  "cases": [
    {"expect": "Block", "files": [{"path": "src/widget.cpp", "text": "..."}]},
    {"expect": "Allow", "files": [{"path": "src/widget.cpp", "text": "..."}]}
  ]
}
```
