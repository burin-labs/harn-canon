# Protocol Buffers Seed Predicate Pack

This pack covers `.proto` schemas — proto2, proto3, and the newer Editions syntax. Protobuf has a small surface area but a brutal failure mode: a renumbered field or a deleted-then-reused tag silently corrupts data on the wire across every consumer that has not yet redeployed. The predicates here target the handful of authoring mistakes that are cheap to catch on a slice and expensive to recover from in production.

## Stack Assumptions

- Schema sources end in `.proto`; generated stubs (`*.pb.go`, `*.pb.cc`, `*_pb2.py`, etc.) are out of scope for this pack — those should be reviewed by the consuming language's pack.
- Vendored or generated proto trees under `/vendor/`, `/third_party/`, `/node_modules/`, `/generated/`, or `/.proto-cache/` are excluded from first-party scans.
- Deterministic predicates use file-text scans until Harn Flow exposes a stable proto descriptor query API.
- Semantic predicates make one cheap judge call over changed `.proto` files and rely on the diff context to compare against the prior schema.
- Advisory rules return `Warn` when official guidance is style-level. Blocking rules are reserved for declarations the protobuf compiler or wire format outright rejects, and for changes that break wire compatibility for already-deployed consumers.

## Predicate Coverage

| Predicate | Mode | Verdict | Purpose |
|---|---|---|---|
| `explicit_syntax_version` | deterministic | Block | Every `.proto` file must declare `syntax = "proto2" / "proto3"` or `edition = "YYYY"` so parsers pick the correct dialect. |
| `package_declaration_required` | deterministic | Warn | Schemas should namespace generated symbols with a dotted `package` to avoid cross-schema collisions. |
| `no_required_in_proto3` | deterministic | Block | proto3 dropped the `required` field rule; the protoc parser rejects it. |
| `field_names_lower_snake_case` | deterministic | Warn | Field names should be `lower_snake_case` so generated bindings stay idiomatic across languages. |
| `enum_zero_value_unspecified` | deterministic | Warn | Enums should start with `<NAME>_UNSPECIFIED = 0` so the default is explicit and forward-compatible. |
| `no_reserved_field_number_range` | deterministic | Block | Field numbers 19000-19999 are reserved by the protobuf implementation and refused by protoc. |
| `no_field_number_renumbering` | semantic | Block | Existing field numbers must stay stable; reusing or repurposing a tag silently corrupts wire-compatible data. |
| `reserved_on_field_removal` | semantic | Block | Deleted fields must be `reserved` so future fields cannot accidentally reuse the freed number or name. |

## Evidence

Evidence scanned on 2026-05-09.

- protobuf.dev programming guides for [proto3](https://protobuf.dev/programming-guides/proto3/), [proto2](https://protobuf.dev/programming-guides/proto2/), and [style](https://protobuf.dev/programming-guides/style/).
- protobuf.dev [best practices: dos and don'ts](https://protobuf.dev/best-practices/dos-donts/) for the wire-compat and enum-zero guidance.
- Editions [overview](https://protobuf.dev/editions/overview/) for the post-syntax declaration form.
- Updating-a-message and deleting-a-field sections of the proto3 and proto2 guides for wire-compat rules.

## Known False Positives

- Regex predicates do not parse protobuf. Block comments, unusual whitespace, and macros (when proto files are templated) can confuse deterministic checks.
- `field_names_lower_snake_case` looks at simple `optional/repeated/required type field = N` shapes; map fields and `oneof` members with type parameters may not match the same regex and can slip through.
- `enum_zero_value_unspecified` scans for the conventional `_UNSPECIFIED = 0` suffix. Some legacy schemas use `_INVALID = 0` or `_NONE = 0` as the sentinel; those will warn until the convention is normalized or a suppression lands.
- `no_reserved_field_number_range` only catches the always-reserved 19000-19999 implementation range. Per-message `reserved` ranges declared in the schema are out of scope for the deterministic check and should be enforced at the descriptor layer once available.
- `no_required_in_proto3` looks for `required` in files that explicitly declare `syntax = "proto3"`. Files using Editions with `features.field_presence = LEGACY_REQUIRED` are out of scope for this check.
- Semantic predicates depend on the judge recognizing the prior shape of the message from diff context. They should stay high-threshold and cite the exact field number, name, or type change before blocking.

## Fixtures

Each fixture in `fixtures/` contains one blocked or warned example and one allowed example for the corresponding predicate. The fixture shape matches the current harn-canon convention:

```json
{
  "predicate": "name",
  "cases": [
    {"expect": "Block", "files": [{"path": "api/v1/user.proto", "text": "..."}]},
    {"expect": "Allow", "files": [{"path": "api/v1/user.proto", "text": "..."}]}
  ]
}
```
