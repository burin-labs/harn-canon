# Harn Seed Predicate Pack

This pack covers Harn scripts, Flow workflows, and agent-facing Harn modules. It is intentionally focused on the mistakes most likely to create nondeterminism, runaway cost, schema drift, or unsafe agent behavior.

## Stack assumptions

- Files use the `.harn` extension and current Harn syntax.
- The Flow predicate runtime provides `Slice`, `Context`, `Repo`, and `ctx.semantic_judge(...)` through Harn.
- Deterministic predicates run over changed Harn source text. They prefer conservative warnings when regex matching can produce false positives.
- Semantic predicates are strict-gate candidates only when the judge can cite a concrete changed span.

## Predicate coverage

| Predicate | Mode | Verdict | Purpose |
|---|---|---|---|
| `llm_call_schema_sets_schema_retries` | deterministic | Block | Schema-mode `llm_call` must opt into schema repair or use `llm_call_structured`. |
| `parallel_io_sets_max_concurrent` | deterministic | Warn | Parallel fan-out that calls LLM, HTTP, host, or MCP tools should cap in-flight work. |
| `no_source_heredocs` | deterministic | Block | Harn source uses triple-quoted strings; heredocs are only valid in tool-call JSON. |
| `no_legacy_transcript_options` | deterministic | Block | Legacy transcript option keys must not be reintroduced. |
| `schema_objects_reject_unknown_properties` | deterministic | Warn | Closed LLM/output schemas should reject unexpected object properties. |
| `dynamic_boundaries_use_unknown` | deterministic | Warn | Dynamic JSON/LLM/tool boundaries should use `unknown` plus schema narrowing, not `any`. |
| `tests_mock_time_for_sleep` | deterministic | Warn | Tests that exercise time, sleep, retry, or deadlines should use mock time. |
| `prefer_enumerate_over_index_loops` | deterministic | Warn | Prefer direct iteration or `.enumerate()` over `range(len(xs))` loops. |
| `emit_channel_sets_stable_id` | deterministic | Warn | Durable channel emits should carry a stable id for replay and retry dedupe. |
| `oauth_redirect_uris_are_https_or_loopback` | deterministic | Block | OAuth dynamic registration metadata must not use plain HTTP web redirect URIs. |
| `llm_prompts_do_not_embed_secrets` | semantic | Block | Prompts must not embed secrets, credentials, or sensitive customer data. |
| `oauth_audit_payloads_redact_tokens` | semantic | Block | OAuth audit, transcript, log, and span payloads must redact credentials and tokens. |
| `acp_tool_side_effects_are_honest` | semantic | Block | ACP tool metadata must describe the strongest side effect a tool can perform. |

## Evidence

Evidence scanned on 2026-04-26 and refreshed for Harn channel/OAuth surfaces on 2026-05-19.

- Harn quick reference: attributes, strings, typing, iteration, JSON querying, concurrency, and time mocking.
- Harn builtins reference: JSON/schema helpers, list methods, string helpers, and regex functions.
- Harn changelog: `llm_call_structured`, schema retries, removed legacy transcript options, durable channel receipts, and `std/oauth/*` client/dynamic-registration redaction contracts.
- OpenAI Structured Outputs guide: schema-backed model outputs and strict structured output behavior.
- OpenAI and Anthropic rate-limit guidance: short bursts and uncapped concurrency can trip provider limits.
- JSON Schema object reference: `properties`, `required`, and `additionalProperties` object validation.
- OWASP, OpenAI, and Microsoft AI security guidance: prompt-injection, system-prompt leakage, sensitive-information disclosure, and excessive-agency risks.
- RFC 7591 and RFC 8252: OAuth dynamic client registration validation and native-app loopback redirect exceptions.
- OWASP Logging Cheat Sheet: data that should be excluded from application logs.

## Known false positives

- Regex predicates are syntax-aware only at the source-text level until Flow exposes a stable Harn AST query API.
- `parallel_io_sets_max_concurrent` warns on helper calls whose names look like external IO, even when a wrapper has its own limiter.
- `schema_objects_reject_unknown_properties` assumes closed schemas by default; extension-point schemas should document intentional `additional_properties`.
- `dynamic_boundaries_use_unknown` is advisory because some low-level generic helpers legitimately use `any`.
- `emit_channel_sets_stable_id` is text-level and may miss ids assembled by wrapper functions; wrappers should carry their own focused invariants.
- `oauth_redirect_uris_are_https_or_loopback` catches literal metadata only. Runtime metadata still relies on `std/oauth/dynamic_registration` validation.
- The semantic predicates depend on a cheap judge. They should stay high-threshold and cite concrete spans before blocking.

## Fixtures

Each fixture in `fixtures/` contains one blocked or warned example and one allowed example for the corresponding predicate. The fixture shape is deliberately simple until the Flow replay harness lands:

```json
{
  "predicate": "name",
  "cases": [
    {"expect": "Block", "files": [{"path": "workflow.harn", "text": "..."}]},
    {"expect": "Allow", "files": [{"path": "workflow.harn", "text": "..."}]}
  ]
}
```
