# Python Seed Predicate Pack

This pack covers general-purpose Python application and library code. It is intentionally focused on mistakes that are cheap to detect in review slices and have a clear operational or security cost: swallowed exceptions, shared mutable defaults, leaked debug output, unsafe dynamic execution, unclosed files, shell injection, production asserts, SQL injection, and hardcoded secrets.

## Stack Assumptions

- Files use the `.py` extension and target modern Python 3.
- Deterministic predicates run over changed Python source text. They are regex-backed until Flow exposes a stable Python AST query API, so lower-confidence checks warn instead of block.
- Production-path checks exclude obvious tests, `cli/`, `script/` or `scripts/`, `cli.py`, `main.py`, and `__main__.py`.
- Semantic predicates use one cheap judge call and should block only when they can cite a concrete changed span.
- Existing project linters such as Ruff, mypy, pyright, Bandit, pytest, and framework-specific checks remain the primary local enforcement tools; this pack seeds portable defaults for Flow.

## Predicate Coverage

| Predicate | Mode | Verdict | Purpose |
|---|---|---|---|
| `no_bare_except` | deterministic | Block | Bare `except:` catches `BaseException`, including interpreter-exiting exceptions. |
| `type_hints_on_pub_fn` | deterministic | Warn | Public top-level functions should expose useful parameter and return annotations. |
| `no_print_in_prod_path` | deterministic | Warn | Production paths should use `logging`; `print` is reserved for tests and CLIs. |
| `no_mutable_default_arg` | deterministic | Block | Mutable defaults share state across calls and cause surprising behavior. |
| `context_mgr_for_files` | deterministic | Warn | File handles should normally be managed with `with open(...)` or `Path.open(...)`. |
| `no_eval_exec` | deterministic | Block | Direct `eval()` and `exec()` calls create arbitrary-code-execution risk. |
| `no_subprocess_shell_true` | deterministic | Block | `subprocess.*(..., shell=True)` raises shell-injection risk. |
| `no_assert_in_prod_path` | deterministic | Warn | Production validation should not rely on asserts that optimized runs can remove. |
| `sql_queries_use_parameters` | semantic | Block | SQL should use DB-API placeholders and bound parameters, not string-built queries. |
| `secrets_not_hardcoded_in_source` | semantic | Block | Credentials and tokens should come from secret managers or scoped environment. |

## Evidence

Evidence scanned on 2026-04-30.

- Python 3.14 documentation: exception handling, default argument values, `with`, `open`, `eval`, `exec`, `subprocess` security, assertions, `typing`, `sqlite3` placeholders, and `logging`.
- Ruff rule documentation: E722 bare except, ANN201 public function annotations, T201 print, B006 mutable argument defaults, S307 eval, S102 exec, S101 assert, S602 subprocess shell, and hardcoded password rules.
- OWASP, CWE-78, and CWE-798 guidance: SQL injection, OS command injection, credential hygiene, and hardcoded credentials.

## Known False Positives

- Regex predicates are syntax-aware only at the source-text level; comments, string literals, aliases, and multiline formatting can fool them.
- `type_hints_on_pub_fn` only catches unannotated top-level functions on a single signature span. It does not fully validate every parameter annotation.
- `context_mgr_for_files` warns on code that intentionally closes file handles elsewhere.
- `no_print_in_prod_path` treats obvious CLI/script/test paths as exempt but cannot infer custom user-output modules.
- `no_eval_exec` may flag intentionally shadowed helper names named `eval` or `exec`.
- `no_subprocess_shell_true` flags all shell use as a block candidate. Rare justified shell usage should move behind a reviewed helper with sanitization.
- The semantic predicates depend on a cheap judge and should stay high-threshold until Flow exposes structured Python taint or data-flow facts.

## Fixtures

Each fixture in `fixtures/` contains one blocked or warned example and one allowed example for the corresponding predicate. The fixture shape mirrors the existing seed packs:

```json
{
  "predicate": "name",
  "cases": [
    {"expect": "Block", "files": [{"path": "app.py", "text": "..."}]},
    {"expect": "Allow", "files": [{"path": "app.py", "text": "..."}]}
  ]
}
```
