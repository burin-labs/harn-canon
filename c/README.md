# C Seed Predicate Pack

This pack covers plain C source and header files for hosted application and library code. It targets the high-signal review issues an Archivist can catch cheaply on changed slices: classic memory and string-handling footguns (`gets`, unbounded copies, format-string vulns), unsafe entry points (`void main`, `tmpnam`/`mktemp`), parsing helpers that swallow errors (`atoi`/`atol`/`atof`), header hygiene, and stack-allocation hazards. Three semantic predicates carry the load that regex cannot: NULL-return checks on heap allocations, evidence of a static-analyzer or sanitizer pipeline, and vulnerability-check evidence for native dependency changes.

## Stack Assumptions

- C source files use `.c`; C headers use `.h`. Files containing only C++ (`.cc`, `.cpp`, `.cxx`, `.hpp`) are out of scope for this pack — see a future C++ pack for those.
- Production paths exclude any path under `test/`, `tests/`, `unittest/`, `unittests/`, and any file matching `*_test.c`, `*_tests.c`, or `test_main.c`.
- Generated C files marked with a top-level `Code generated ... DO NOT EDIT` or `Auto-generated ... DO NOT EDIT` comment are ignored by deterministic source predicates.
- Deterministic predicates use file-text regex scans because Harn Flow does not yet expose a stable C AST or preprocessor query API.
- Semantic predicates make a single judge call over changed C and project files using only evidence captured at authoring time.
- Hosted environment is assumed (i.e., `int main` is required). Freestanding builds (kernel, embedded firmware, microcontrollers) should suppress `no_void_main` locally once the predicate runtime supports suppressions.

## Predicate Coverage

| Predicate | Mode | Verdict | Purpose |
|---|---|---|---|
| `no_gets` | deterministic | Block | `gets()` has no length bound and was removed from the C standard library in C11; there is no safe call site. |
| `bounded_string_ops` | deterministic | Warn | `strcpy`, `strcat`, `sprintf`, `vsprintf`, and `scanf` cannot accept a length bound; bounded variants exist for each. |
| `no_void_main` | deterministic | Block | Hosted-environment programs must declare `main` with `int` return type; `void main` is undefined behavior on most exit paths. |
| `no_format_string_from_variable` | deterministic | Block | Passing a non-literal as the format argument is the standard format-string vulnerability (CWE-134). |
| `no_unsafe_tmpfile` | deterministic | Block | `tmpnam`, `tempnam`, and `mktemp` choose a name and leave a TOCTOU window before `open`. |
| `no_atoi_family` | deterministic | Warn | `atoi`/`atol`/`atoll`/`atof` cannot signal conversion failure or overflow; `strtol`/`strtoul`/`strtod` can. |
| `c_header_has_include_guard` | deterministic | Warn | C headers must be safe to include multiple times; missing guards cause redefinition errors and ODR-style problems. |
| `no_alloca` | deterministic | Warn | `alloca` and dynamic VLAs sized by user input can silently exhaust the stack; behavior on overflow is implementation-defined. |
| `allocation_return_checked` | semantic | Block | Heap allocators (`malloc`/`calloc`/`realloc`/`strdup`/`asprintf`) can return NULL; using the result without a check is undefined behavior. |
| `static_analyzer_clean` | semantic | Block | Pointer arithmetic, manual memory management, parsing, and concurrency primitives benefit from clang-analyzer / cppcheck / sanitizer coverage; the change should show evidence one of those is wired up. |
| `c_dependency_security_checked` | semantic | Block | Native dependency manifests (CMake/Make/conan/vcpkg/meson) and CI changes should preserve a CVE/OSV/Dependabot review path. |

## Evidence

Evidence scanned on 2026-05-10.

- **Linux man pages (man7.org)**: `gets(3)`, `fgets(3p)`, `strncpy(3)`, `snprintf(3)`, `printf(3)`, `mkstemp(3)`, `tmpnam(3)`, `strtol(3)`, `atoi(3)`, `malloc(3)`, `alloca(3)`.
- **GNU C Library Reference Manual**: program arguments and `main`, copying strings and arrays, parsing of integers, variable-size automatic storage, unconstrained allocation.
- **GCC Preprocessor Manual**: once-only headers (canonical `#pragma once` / `#ifndef` guidance).
- **ISO C standard**: ISO/IEC 9899:1999 working draft (N1570) for hosted-environment `main` signature.
- **CWE / MITRE**: CWE-120 (classic buffer overflow), CWE-134 (uncontrolled format string), CWE-242 (use of inherently dangerous function), CWE-377 (insecure temporary file), CWE-690 (unchecked return value to NULL pointer dereference).
- **OWASP**: Format String Attack reference, Source Code Analysis Tools index.
- **Static-analysis and sanitizer tooling**: Clang Static Analyzer, Cppcheck manual, Google Sanitizers wiki (AddressSanitizer/UBSan/MSan/TSan).
- **Style guides**: Google C++ Style Guide on `#define` header guards (applies cleanly to C).
- **Dependency security**: OSV.dev, Microsoft `vcpkg` docs, Conan 2.x requirements docs, GitHub Dependabot configuration docs.

## Known False Positives

- Regex predicates do not parse C. Macro-expanded names, comments containing the function names, string-literal arguments quoting the names, and unusual whitespace can confuse deterministic checks.
- `no_format_string_from_variable` matches conservative patterns: a bare identifier as the format argument for `printf`/`vprintf`/`sprintf`/`vsprintf`, the second argument for `fprintf`/`dprintf`/`vfprintf`/`syslog`, and the third argument for `snprintf`/`vsnprintf`. Helper wrappers that take a `va_list` and call-expression format arguments such as `printf(get_msg())` are false negatives this predicate intentionally does not cover; rely on `static_analyzer_clean` (clang-analyzer's `-Wformat-nonliteral`) for those. Calls that build the format via `strcat` and then pass the buffer are likewise covered by `static_analyzer_clean` or `bounded_string_ops`.
- `bounded_string_ops` flags any use, including cases where the length is statically provable (e.g. `sprintf(buf, "%d", id)` into a sufficiently large buffer). It is intentionally a Warn so reviewers can confirm the bound rather than rewriting.
- `no_void_main` only inspects `.c` source files. It does not catch `void main` declared in a header that is then defined elsewhere; that pattern is exotic enough that the noise of scanning headers was not worth it.
- `c_header_has_include_guard` accepts both `#pragma once` and the canonical `#ifndef`/`#define`/`#endif` triple. Headers that wrap their entire body in a single conditional for unrelated reasons are a rare false positive.
- `no_alloca` does not currently flag VLAs (variable-length arrays). VLA detection without an AST has too high a false-positive rate; the semantic `static_analyzer_clean` predicate covers the common case via clang-analyzer.
- Semantic predicates depend on the judge recognizing concrete changed spans. They should stay high-threshold and cite exact code or build-config evidence before blocking.

## Fixtures

Each fixture in `fixtures/` contains at least one blocked or warned example and at least one allowed example for the corresponding predicate. The fixture shape matches the harn-canon convention:

```json
{
  "predicate": "name",
  "cases": [
    {"expect": "Block", "files": [{"path": "src/parser.c", "text": "..."}]},
    {"expect": "Allow", "files": [{"path": "src/parser.c", "text": "..."}]}
  ]
}
```
