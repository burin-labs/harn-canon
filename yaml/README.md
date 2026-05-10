# YAML Seed Predicate Pack

This pack covers plain YAML configuration before stack-specific packs (Kubernetes, GitHub Actions, Ansible, Helm) layer tighter rules on top. YAML's surface area is small but its parser quirks are loud, so the v0 set focuses on long-known footguns: tab indentation, the YAML 1.1 vs 1.2 boolean drift (the "Norway problem"), bare scalars that parsers re-type, the cross-document anchor scope rule, and language-specific object tags that are remote-code-execution sinks.

## Stack Assumptions

- Source checks target `.yaml` and `.yml` files.
- Syntactic predicates skip YAML living under `fixtures/`, `__fixtures__/`, `testdata/`, `test-data/`, `test/`, `tests/`, and `spec/` paths because parser fixtures intentionally include malformed input. Security predicates (`no_unsafe_yaml_tags`, `no_hardcoded_secrets`) and `yamllint_compliance` still check those paths.
- Deterministic predicates run over changed source text until Flow exposes a stable YAML AST query API. Rules with meaningful false-positive risk warn rather than block.
- Semantic predicates use one cheap judge call and should block only when they can cite a concrete changed span.

## Predicate Coverage

| Predicate | Mode | Verdict | Purpose |
|---|---|---|---|
| `no_tabs_for_indent` | deterministic | Block | YAML 1.2 forbids tabs as indentation; loaders error inconsistently. |
| `explicit_boolean_types` | deterministic | Warn | Bare `yes`/`no`/`on`/`off`/`y`/`n` change meaning between YAML 1.1 and 1.2 parsers. |
| `quoted_ambiguous_scalars` | deterministic | Warn | Trailing-zero versions, leading-zero ids, and `12:34:56`-shaped scalars must be quoted to stay strings. |
| `consistent_indent` | deterministic | Warn | Lines indented by an odd number of spaces almost always indicate a broken indent step. |
| `no_unsafe_yaml_tags` | deterministic | Block | `!!python/object`, `!ruby/object`, `!!java`, and similar tags are RCE sinks under unsafe loaders. |
| `no_anchors_across_docs` | deterministic | Warn | Anchors reset at every `---`; aliases across documents resolve to nothing or to a stale anchor. |
| `yamllint_compliance` | semantic | Block | Catches errors yamllint's default profile would surface: duplicate keys, empty required values, parser-fatal syntax. |
| `no_hardcoded_secrets` | semantic | Block | API keys, tokens, private keys, and production connection strings must come from a secret store. |

## Evidence

Evidence scanned on 2026-05-09.

- YAML 1.2.2 specification: indentation (§6.1), boolean tag resolution (§10.2.1.2), tag resolution (§10.3.2), node anchors (§6.9.2), and YAML streams (§9.2).
- yamllint stable rules and configuration documentation: `indentation`, `truthy`, `quoted-strings`, `key-duplicates`, plus the rules index and configuration reference.
- PyYAML documentation on safe vs full loaders, and the OWASP Deserialization Cheat Sheet for unsafe-tag risk and remediation.
- OWASP Secrets Management Cheat Sheet and GitHub secret-scanning documentation for hardcoded credential risk and remediation context.

## Known False Positives

- All deterministic predicates run on raw source text. Comments, block scalars, multi-line quoted strings, and flow-style mappings can fool simple regexes until AST-level matching lands.
- `no_tabs_for_indent` does not distinguish a tab inside a quoted string from a tab used as indentation; tabs inside string content are rare in practice but will trigger the block.
- `explicit_boolean_types` only flags bare values after `key:`. Block-scalar children, flow-style sequences, and multi-line strings can hide an offending value.
- `quoted_ambiguous_scalars` is intentionally narrow: it covers the three highest-signal shapes (`0\d+`, `\d+\.\d+0`, sexagesimal). Other ambiguous bare scalars (`null`, `~`, `NaN`, `.inf`) are left to `yamllint_compliance` and stack-specific packs.
- `consistent_indent` warns on any line indented by 1, 3, 5, or 7 spaces. Some hand-formatted multi-line block scalars or comments may exceed this and trip the warn.
- `no_anchors_across_docs` warns at file granularity whenever a multi-document YAML file uses any alias; an alias that genuinely references a same-document anchor will still warn until structural matching lands.
- `no_unsafe_yaml_tags` blocks all language-specific `!!lang/` tags. A repo that intentionally uses `!!python/object` with a safe whitelisted loader would still need to suppress this rule.
- The semantic predicates depend on a cheap judge call and stay high-threshold; they should not block on speculative concerns.

## Fixtures

Each fixture in `fixtures/` contains one blocked or warned example and one allowed example for the corresponding predicate. The fixture shape mirrors the existing seed packs:

```json
{
  "predicate": "name",
  "cases": [
    {"expect": "Block", "files": [{"path": "config/app.yaml", "text": "..."}]},
    {"expect": "Allow", "files": [{"path": "config/app.yaml", "text": "..."}]}
  ]
}
```
