# GraphQL Seed Predicate Pack

This pack covers GraphQL schema files (`.graphql`, `.graphqls`, `.gql`) and the server wiring that hosts them. The surface area is small relative to a full language pack, so v0 prioritizes high-signal naming, documentation, evolution, and resource-bound rules drawn from the GraphQL spec, the Apollo schema-design tech notes, the Relay connection spec, and the OWASP GraphQL cheat sheet.

## Stack Assumptions

- Schema checks target `.graphql`, `.graphqls`, and `.gql` files. Generated paths (`/generated/`, `/__generated__/`, `*.generated.*`) are excluded.
- Schemas are written in GraphQL SDL, not introspected JSON; client document linting belongs in a separate pack.
- The server-config check is intentionally framework-broad: Apollo Server, Apollo Router, GraphQL Yoga, Mercurius, gqlgen, graphql-ruby, Strawberry, Ariadne, and similar all qualify.
- Deterministic predicates run over changed schema source text. AST queries will replace the regexes once Flow exposes a stable GraphQL query API.
- Semantic predicates use `ctx.semantic_judge(...)` and must cite concrete changed spans before blocking; schema-evolution checks rely on the judge to reason about the diff until the runtime exposes paired base-and-head schema snapshots.

## Predicate Coverage

| Predicate | Mode | Verdict | Purpose |
|---|---|---|---|
| `enum_values_upper_snake_case` | deterministic | Block | Enum values follow the Apollo and graphql-eslint UPPER_SNAKE_CASE convention. |
| `no_double_underscore_names` | deterministic | Block | The GraphQL spec reserves a leading double underscore for introspection. |
| `descriptions_on_public_types` | deterministic | Warn | Schema files declaring public types should carry at least one description block. |
| `mutation_uses_input_type` | deterministic | Warn | Mutations should take a single `input` object so callers can evolve fields safely. |
| `pagination_args_on_root_list_fields` | deterministic | Warn | Root Query list fields should expose pagination arguments to bound result size. |
| `no_breaking_schema_change` | semantic | Block | Schema changes must keep a backwards-compatible alias or staging path for removed or narrowed elements. |
| `deprecation_over_removal` | semantic | Block | Public schema elements must be `@deprecated` with a reason before removal. |
| `query_depth_limit_enforced` | semantic | Block | Public GraphQL endpoints must configure a depth, complexity, alias, token, or persisted-operation limit. |

## Evidence

Evidence scanned on 2026-05-09.

- GraphQL October 2021 specification: reserved names (§ 2.1.9), descriptions (§ 2.4), and the `@deprecated` directive.
- graphql.org learn pages: introspection, pagination, and best-practices guidance on schema versioning.
- Apollo schema design tech notes: TN0002 schema naming conventions and the GraphOS schema-checks workflow.
- Apollo Router operation-limits configuration for depth, complexity, alias, and token bounds.
- Relay specifications: cursor connections for pagination and the mutation input-object convention.
- The Guild graphql-eslint rule documentation: `naming-convention` and `require-description`.
- The Guild graphql-inspector docs for diff-based breaking-change detection.
- OWASP GraphQL Security Cheat Sheet for query-cost and depth-limit guidance.

## Known False Positives

- `enum_values_upper_snake_case` is line-anchored: an enum value that starts with an uppercase letter but contains lowercase mid-identifier (`MixedCase`) is not flagged until AST checks land.
- `no_double_underscore_names` matches type and field declaration sites only; it does not inspect references to introspection types in queries.
- `descriptions_on_public_types` warns at file granularity. A schema file with one description and many undocumented types is currently treated as documented.
- `mutation_uses_input_type` flags any mutation whose first argument is not named `input`, which can be noisy for projects that intentionally take a single scalar argument such as `id`.
- `pagination_args_on_root_list_fields` only inspects bare `name: [...]` and `name(): [...]` shapes; a list field that takes filter arguments but no pagination cursor is not yet flagged.
- The semantic predicates depend on the judge being able to reason about removals or server wiring from the changed slice; until the runtime exposes paired base-and-head schemas and richer change context, blocking should stay anchored to clear, citable spans.

## Fixtures

Each fixture in `fixtures/` contains at least one blocked or warned example and one allowed example for the corresponding predicate:

```json
{
  "predicate": "name",
  "cases": [
    {"expect": "Block", "files": [{"path": "schema/user.graphql", "text": "..."}]},
    {"expect": "Allow", "files": [{"path": "schema/user.graphql", "text": "..."}]}
  ]
}
```
