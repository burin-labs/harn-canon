#!/usr/bin/env python3
import argparse
import base64
import json
import subprocess
import sys
import tempfile
from pathlib import Path

from validate_canon import EXPECTED_PACKS, ROOT, parse_invariants

HARN_TIMEOUT_SECONDS = 30


def harn_string_literal(value):
    return json.dumps(value, ensure_ascii=False)


def load_fixture(pack_dir, predicate):
    fixture_path = pack_dir / "fixtures" / f"{predicate}.json"
    return json.loads(fixture_path.read_text(encoding="utf-8"))


def wrapper_source(pack, deterministic_entries):
    invariants_path = f"{pack}/invariants.harn"
    lines = [
        "fn flow_fixture_verdict(record) {",
        '  let kind = to_string(record?.result?.verdict?.kind ?? record?.raw_result?.verdict ?? "")',
        "  let normalized = kind.lower()",
        '  if normalized == "allow" { return "Allow" }',
        '  if normalized == "warn" { return "Warn" }',
        '  if normalized == "block" { return "Block" }',
        '  if normalized == "require_approval" { return "RequireApproval" }',
        '  return kind == "" ? "Missing" : kind',
        "}",
        "",
        "fn main(harness: Harness) {",
        "  var failures = []",
        "  var executed = 0",
    ]

    counter = 0
    for entry in deterministic_entries:
        predicate = entry["name"]
        fixture = load_fixture(ROOT / pack, predicate)
        for case in fixture["cases"]:
            files_json = json.dumps(case["files"], ensure_ascii=False, separators=(",", ":"))
            files_literal = harn_string_literal(
                base64.b64encode(files_json.encode("utf-8")).decode("ascii")
            )
            case_name = case["name"]
            expect = case["expect"]
            lines.extend(
                [
                    f"  let files_{counter} = json_parse(base64_decode({files_literal}))",
                    f"  let eval_{counter} = flow_evaluate_invariants(",
                    '    "",',
                    f"    {{files: files_{counter}}},",
                    "    {",
                    f"      path: {harn_string_literal(invariants_path)},",
                    f"      predicates: [{harn_string_literal(predicate)}],",
                    "      budget_ms: 50,",
                    "    },",
                    "  )",
                    f"  let records_{counter} = eval_{counter}.records ?? []",
                    f"  let record_{counter} = if len(records_{counter}) > 0 {{ records_{counter}[0] }} else {{ nil }}",
                    f"  let actual_{counter} = flow_fixture_verdict(record_{counter})",
                    "  executed = executed + 1",
                    f"  if actual_{counter} != {harn_string_literal(expect)} {{",
                    "    failures = failures.push({",
                    f'      pack: "{pack}",',
                    f'      predicate: "{predicate}",',
                    f"      case: {harn_string_literal(case_name)},",
                    f"      expect: {harn_string_literal(expect)},",
                    f"      actual: actual_{counter},",
                    f"      result: record_{counter} ?? eval_{counter},",
                    "    })",
                    "  }",
                ]
            )
            counter += 1

    lines.extend(
        [
            "  __io_println(json_stringify({executed: executed, failures: failures}))",
            "}",
            "",
        ]
    )
    return "\n".join(lines)


def run_pack(pack):
    pack_dir = ROOT / pack
    invariants_path = pack_dir / "invariants.harn"
    errors = []
    entries, _evidence = parse_invariants(invariants_path, errors)
    if errors:
        return {
            "pack": pack,
            "executed": 0,
            "skipped_semantic": 0,
            "failures": [{"error": error} for error in errors],
        }

    deterministic = [entry for entry in entries if entry["mode"] == "deterministic"]
    skipped_semantic = sum(1 for entry in entries if entry["mode"] == "semantic")
    source = wrapper_source(pack, deterministic)

    with tempfile.NamedTemporaryFile(
        "w",
        encoding="utf-8",
        dir=ROOT,
        prefix=".canon-fixtures-",
        suffix=".harn",
        delete=False,
    ) as handle:
        handle.write(source)
        script_path = Path(handle.name)

    try:
        proc = subprocess.run(
            ["harn", "run", str(script_path)],
            cwd=ROOT,
            text=True,
            capture_output=True,
            timeout=HARN_TIMEOUT_SECONDS,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        return {
            "pack": pack,
            "executed": 0,
            "skipped_semantic": skipped_semantic,
            "failures": [
                {
                    "error": f"harn run timed out after {HARN_TIMEOUT_SECONDS}s",
                    "stdout": exc.stdout or "",
                    "stderr": exc.stderr or "",
                }
            ],
        }
    finally:
        script_path.unlink(missing_ok=True)

    if proc.returncode != 0:
        return {
            "pack": pack,
            "executed": 0,
            "skipped_semantic": skipped_semantic,
            "failures": [
                {
                    "error": f"harn run exited {proc.returncode}",
                    "stdout": proc.stdout,
                    "stderr": proc.stderr,
                }
            ],
        }

    payload = None
    for line in reversed(proc.stdout.splitlines()):
        stripped = line.strip()
        if not stripped:
            continue
        try:
            payload = json.loads(stripped)
            break
        except json.JSONDecodeError:
            continue

    if not isinstance(payload, dict):
        return {
            "pack": pack,
            "executed": 0,
            "skipped_semantic": skipped_semantic,
            "failures": [
                {
                    "error": "harn wrapper produced no JSON payload",
                    "stdout": proc.stdout,
                    "stderr": proc.stderr,
                }
            ],
        }

    return {
        "pack": pack,
        "executed": int(payload.get("executed", 0)),
        "skipped_semantic": skipped_semantic,
        "failures": payload.get("failures", []),
    }


def main():
    parser = argparse.ArgumentParser(
        description="Execute deterministic harn-canon fixtures against their Harn predicates."
    )
    parser.add_argument(
        "--pack",
        action="append",
        choices=EXPECTED_PACKS,
        help="Run only one pack. May be repeated.",
    )
    args = parser.parse_args()

    packs = args.pack or EXPECTED_PACKS
    reports = [run_pack(pack) for pack in packs]
    failures = [failure for report in reports for failure in report["failures"]]
    executed = sum(report["executed"] for report in reports)
    skipped_semantic = sum(report["skipped_semantic"] for report in reports)

    if failures:
        print("Canon fixture execution failed:", file=sys.stderr)
        for report in reports:
            for failure in report["failures"]:
                print(
                    f"- {report['pack']}: {json.dumps(failure, ensure_ascii=False, sort_keys=True)}",
                    file=sys.stderr,
                )
        return 1

    print(
        f"Executed {executed} deterministic fixture cases across {len(packs)} packs; "
        f"skipped {skipped_semantic} semantic predicates."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
