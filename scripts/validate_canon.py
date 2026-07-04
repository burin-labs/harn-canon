#!/usr/bin/env python3
import calendar
from collections import Counter
import datetime as dt
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PACK_MANIFEST_PATH = ROOT / "canon-packs.json"


def load_pack_manifest():
    manifest = json.loads(PACK_MANIFEST_PATH.read_text(encoding="utf-8"))
    packs = manifest.get("packs", [])
    if manifest.get("schema_version") != 1 or not isinstance(packs, list):
        raise ValueError("canon-packs.json must use schema_version 1 with a packs list")
    return packs


PACK_MANIFEST = load_pack_manifest()
EXPECTED_PACKS = tuple(pack["id"] for pack in PACK_MANIFEST)

EVAL_CRITICAL_PACK_ROUTES = {
    "c": {"extensions": {"c", "h"}},
    "cpp": {"extensions": {"cc", "cpp", "cxx", "h", "hh", "hpp", "hxx"}},
    "csharp": {"extensions": {"cs"}},
    "go": {"extensions": {"go"}},
    "rust": {"extensions": {"rs"}},
    "scala": {"extensions": {"sc", "scala"}},
    "swift": {"extensions": {"swift"}},
    "typescript": {"extensions": {"ts", "tsx"}},
    "zig": {"extensions": {"zig"}},
}

MIN_DETERMINISTIC = 5
MAX_DETERMINISTIC = 12
MIN_SEMANTIC = 2
MAX_SEMANTIC = 3
PACK_DETERMINISTIC_LIMITS = {
    # Zig carries current-stdlib migration predicates plus the AST-based
    # observe-before-assert grounding detector; keep the exception scoped.
    "zig": (MIN_DETERMINISTIC, 15),
}
VALID_EXPECTS = {"Allow", "Warn", "Block"}
FIXTURE_KEYS = {"predicate", "cases"}
CASE_KEYS = {"name", "expect", "files"}
FILE_KEYS = {"path", "text"}
PACK_MANIFEST_KEYS = {
    "id",
    "title",
    "invariants",
    "fixtures",
    "extensions",
    "file_names",
}
ROUTING_SELECTOR_RE = re.compile(r"[a-z0-9][a-z0-9_+-]*\Z")

INVARIANT_RE = re.compile(
    r"@invariant\s*"
    r"@(?P<mode>deterministic|semantic)(?P<mode_args>\s*\([^)]*\))?\s*"
    r"@archivist\(\s*"
    r"evidence:\s*(?P<evidence>_EVIDENCE_[A-Za-z0-9_]+)\s*,\s*"
    r"confidence:\s*(?P<confidence>(?:0(?:\.\d+)?|1(?:\.0+)?))\s*,\s*"
    r'source_date:\s*"(?P<source_date>\d{4}-\d{2}-\d{2})"\s*'
    r"\).*?"
    r"pub\s+fn\s+(?P<name>[A-Za-z_][A-Za-z0-9_]*)\s*\(",
    re.S,
)
EVIDENCE_RE = re.compile(r"let\s+(_EVIDENCE_[A-Za-z0-9_]+)\s*=\s*\[(.*?)\]", re.S)
URL_RE = re.compile(r'"(https?://[^"]+)"')
SEMANTIC_FALLBACK_RE = re.compile(
    r"""
    fallback\s*:\s*
    (?:
      "(?P<quoted>[A-Za-z_][A-Za-z0-9_]*)"
      |
      (?P<bare>[A-Za-z_][A-Za-z0-9_]*)
    )
    """,
    re.X,
)
FIXTURE_CASE_NAME_RE = re.compile(r"[a-z][a-z0-9_]*\Z")


def shifted_months(day, months):
    month_index = day.year * 12 + (day.month - 1) + months
    year, zero_based_month = divmod(month_index, 12)
    month = zero_based_month + 1
    capped_day = min(day.day, calendar.monthrange(year, month)[1])
    return dt.date(year, month, capped_day)


def duplicate_values(values):
    return sorted(value for value, count in Counter(values).items() if count > 1)


def validate_allowed_keys(rel_path, location, value, allowed, errors):
    unknown = sorted(set(value) - allowed)
    if unknown:
        errors.append(f"{rel_path}: {location} has unknown keys: {', '.join(unknown)}")


def is_normalized_relative_path(value):
    parts = value.split("/")
    return (
        not value.startswith("/")
        and "\\" not in value
        and all(part not in {"", ".", ".."} for part in parts)
    )


def validate_routing_selectors(pack_id, pack, errors):
    extensions = pack.get("extensions", [])
    file_names = pack.get("file_names", [])
    for field, values in (("extensions", extensions), ("file_names", file_names)):
        if not isinstance(values, list):
            errors.append(f"canon-packs.json: {pack_id} {field} must be a list")
            continue
        if values != sorted(values):
            errors.append(f"canon-packs.json: {pack_id} {field} must be sorted")
        duplicates = duplicate_values(values)
        if duplicates:
            errors.append(
                f"canon-packs.json: {pack_id} {field} has duplicates: {', '.join(duplicates)}"
            )
        for value in values:
            if not isinstance(value, str) or not value:
                errors.append(f"canon-packs.json: {pack_id} {field} entries must be strings")
                continue
            if value != value.lower():
                errors.append(
                    f"canon-packs.json: {pack_id} {field} entry {value} must be lowercase"
                )
            if "/" in value or "\\" in value or value.startswith("."):
                errors.append(
                    f"canon-packs.json: {pack_id} {field} entry {value} must be a basename selector"
                )
            if ROUTING_SELECTOR_RE.fullmatch(value) is None:
                errors.append(
                    f"canon-packs.json: {pack_id} {field} entry {value} has invalid characters"
                )

    if not extensions and not file_names:
        errors.append(
            f"canon-packs.json: {pack_id} needs at least one extension or file_names selector"
        )


def parse_invariants(path, errors):
    text = path.read_text(encoding="utf-8")
    entries = []
    for match in INVARIANT_RE.finditer(text):
        entry = match.groupdict()
        mode_args = entry.get("mode_args") or ""
        fallback_match = SEMANTIC_FALLBACK_RE.search(mode_args)
        entry["fallback"] = (
            fallback_match.group("quoted") or fallback_match.group("bare")
            if fallback_match
            else None
        )
        entries.append(entry)

    invariant_count = len(re.findall(r"@invariant\b", text))
    if invariant_count != len(entries):
        errors.append(
            f"{path.relative_to(ROOT)}: parsed {len(entries)} annotated pub fns but found {invariant_count} @invariant markers"
        )

    evidence_defs = {}
    for name, body in EVIDENCE_RE.findall(text):
        evidence_defs[name] = sorted(set(URL_RE.findall(body)))

    return entries, evidence_defs


def validate_evidence(pack, entries, evidence_defs, errors):
    today = dt.date.today()
    cutoff = shifted_months(today, -18)

    for entry in entries:
        predicate = entry["name"]
        evidence_name = entry["evidence"]
        urls = evidence_defs.get(evidence_name)
        if urls is None:
            errors.append(f"{pack}: {predicate} references missing evidence {evidence_name}")
        elif len(urls) < 2:
            errors.append(f"{pack}: {evidence_name} must list at least two evidence URLs")

        confidence = float(entry["confidence"])
        if not 0.0 <= confidence <= 1.0:
            errors.append(f"{pack}: {predicate} confidence {confidence} is outside 0.0..1.0")

        try:
            source_date = dt.date.fromisoformat(entry["source_date"])
        except ValueError:
            errors.append(f"{pack}: {predicate} has invalid source_date {entry['source_date']}")
            continue

        if source_date > today:
            errors.append(f"{pack}: {predicate} source_date {source_date} is in the future")
        if source_date < cutoff:
            errors.append(f"{pack}: {predicate} source_date {source_date} is older than 18 months")


def validate_semantic_fallbacks(pack, entries, errors):
    deterministic_names = {entry["name"] for entry in entries if entry["mode"] == "deterministic"}
    for entry in entries:
        predicate = entry["name"]
        fallback = entry.get("fallback")
        if entry["mode"] == "deterministic":
            if entry.get("mode_args"):
                errors.append(
                    f"{pack}: deterministic predicate {predicate} must not declare mode args"
                )
            continue

        if fallback is None:
            errors.append(
                f"{pack}: semantic predicate {predicate} must declare "
                "@semantic(fallback: deterministic_predicate)"
            )
        elif fallback not in deterministic_names:
            errors.append(
                f"{pack}: semantic predicate {predicate} fallback {fallback} is not a "
                "deterministic predicate in the same pack"
            )


def validate_fixtures(pack_dir, predicate_names, errors):
    fixtures_dir = pack_dir / "fixtures"
    if not fixtures_dir.is_dir():
        errors.append(f"{pack_dir.name}: missing fixtures/ directory")
        return 0

    fixture_files = sorted(fixtures_dir.glob("*.json"))
    fixture_names = {path.stem for path in fixture_files}

    missing = sorted(predicate_names - fixture_names)
    extra = sorted(fixture_names - predicate_names)
    if missing:
        errors.append(f"{pack_dir.name}: missing fixture files for {', '.join(missing)}")
    if extra:
        errors.append(f"{pack_dir.name}: fixture files without predicates: {', '.join(extra)}")

    for fixture_path in fixture_files:
        rel_path = fixture_path.relative_to(ROOT)
        try:
            fixture = json.loads(fixture_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            errors.append(f"{rel_path}: invalid JSON: {exc}")
            continue

        if not isinstance(fixture, dict):
            errors.append(f"{rel_path}: fixture must be an object")
            continue

        if fixture.get("predicate") != fixture_path.stem:
            errors.append(f"{rel_path}: predicate must match fixture file name")

        cases = fixture.get("cases")
        if not isinstance(cases, list) or not cases:
            errors.append(f"{rel_path}: cases must be a non-empty list")
            continue
        validate_allowed_keys(rel_path, "fixture", fixture, FIXTURE_KEYS, errors)

        expects = set()
        case_names = []
        for index, case in enumerate(cases):
            if not isinstance(case, dict):
                errors.append(f"{rel_path}: case {index} must be an object")
                continue
            validate_allowed_keys(rel_path, f"case {index}", case, CASE_KEYS, errors)

            case_name = case.get("name")
            if not isinstance(case_name, str) or not case_name:
                errors.append(f"{rel_path}: case {index} needs a name")
            elif FIXTURE_CASE_NAME_RE.fullmatch(case_name) is None:
                errors.append(f"{rel_path}: case {index} name must be snake_case")
            else:
                case_names.append(case_name)

            expect = case.get("expect")
            if expect not in VALID_EXPECTS:
                errors.append(f"{rel_path}: case {index} has invalid expect {expect!r}")
            else:
                expects.add(expect)

            files = case.get("files")
            if not isinstance(files, list) or not files:
                errors.append(f"{rel_path}: case {index} files must be a non-empty list")
                continue

            for file_index, file_fixture in enumerate(files):
                if not isinstance(file_fixture, dict):
                    errors.append(f"{rel_path}: case {index} file {file_index} must be an object")
                    continue
                validate_allowed_keys(
                    rel_path,
                    f"case {index} file {file_index}",
                    file_fixture,
                    FILE_KEYS,
                    errors,
                )

                file_path = file_fixture.get("path")
                if not isinstance(file_path, str) or not file_path:
                    errors.append(f"{rel_path}: case {index} file {file_index} needs a path")
                elif not is_normalized_relative_path(file_path):
                    errors.append(
                        f"{rel_path}: case {index} file {file_index} path must be normalized and relative"
                    )
                if not isinstance(file_fixture.get("text"), str):
                    errors.append(f"{rel_path}: case {index} file {file_index} needs text")

        duplicate_case_names = duplicate_values(case_names)
        if duplicate_case_names:
            errors.append(f"{rel_path}: duplicate case names: {', '.join(duplicate_case_names)}")

        if "Allow" not in expects:
            errors.append(f"{rel_path}: fixture must include at least one Allow case")
        if not (expects & {"Warn", "Block"}):
            errors.append(f"{rel_path}: fixture must include at least one Warn or Block case")

    return len(fixture_files)


def validate_readme_coverage(errors):
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    for pack in EXPECTED_PACKS:
        if f"](./{pack}/)" not in readme:
            errors.append(f"README.md: missing pack link for {pack}/")


def validate_manifest(errors):
    seen = set()
    packs_by_id = {}
    for index, pack in enumerate(PACK_MANIFEST):
        if not isinstance(pack, dict):
            errors.append(f"canon-packs.json: pack {index} must be an object")
            continue
        validate_allowed_keys(
            "canon-packs.json",
            f"pack {index}",
            pack,
            PACK_MANIFEST_KEYS,
            errors,
        )
        pack_id = pack.get("id")
        if not isinstance(pack_id, str) or not pack_id:
            errors.append(f"canon-packs.json: pack {index} needs a non-empty id")
            continue
        if pack_id in seen:
            errors.append(f"canon-packs.json: duplicate pack id {pack_id}")
        seen.add(pack_id)
        packs_by_id[pack_id] = pack
        expected_invariants = f"{pack_id}/invariants.harn"
        expected_fixtures = f"{pack_id}/fixtures"
        if pack.get("invariants") != expected_invariants:
            errors.append(
                f"canon-packs.json: {pack_id} invariants must be {expected_invariants}"
            )
        if pack.get("fixtures") != expected_fixtures:
            errors.append(f"canon-packs.json: {pack_id} fixtures must be {expected_fixtures}")
        if not isinstance(pack.get("title"), str) or not pack["title"].strip():
            errors.append(f"canon-packs.json: {pack_id} needs a non-empty title")
        if not (ROOT / expected_invariants).is_file():
            errors.append(f"canon-packs.json: {expected_invariants} does not exist")
        if not (ROOT / expected_fixtures).is_dir():
            errors.append(f"canon-packs.json: {expected_fixtures} does not exist")
        validate_routing_selectors(pack_id, pack, errors)

    validate_eval_critical_routes(packs_by_id, errors)


def validate_eval_critical_routes(packs_by_id, errors):
    for pack_id, required in EVAL_CRITICAL_PACK_ROUTES.items():
        pack = packs_by_id.get(pack_id)
        if pack is None:
            errors.append(f"canon-packs.json: missing eval-critical pack {pack_id}")
            continue

        for field, expected_values in required.items():
            actual_values = set(pack.get(field, []))
            missing = sorted(expected_values - actual_values)
            if missing:
                errors.append(
                    f"canon-packs.json: eval-critical pack {pack_id} {field} "
                    f"must include {', '.join(missing)}"
                )


def validate_pack_readme_coverage(pack_dir, predicate_names, errors):
    readme_path = pack_dir / "README.md"
    readme = readme_path.read_text(encoding="utf-8")
    missing = sorted(name for name in predicate_names if name not in readme)
    if missing:
        errors.append(f"{readme_path.relative_to(ROOT)}: missing predicate coverage for {', '.join(missing)}")


def main():
    errors = []
    expected = set(EXPECTED_PACKS)
    actual = {path.name for path in ROOT.iterdir() if (path / "invariants.harn").is_file()}

    for pack in sorted(expected - actual):
        errors.append(f"{pack}: expected pack directory is missing")
    for pack in sorted(actual - expected):
        errors.append(f"{pack}: pack directory is not listed in EXPECTED_PACKS")

    validate_manifest(errors)
    validate_readme_coverage(errors)

    total_predicates = 0
    total_fixtures = 0
    for pack in EXPECTED_PACKS:
        pack_dir = ROOT / pack
        invariants_path = pack_dir / "invariants.harn"
        readme_path = pack_dir / "README.md"

        if not invariants_path.is_file() or not readme_path.is_file():
            continue

        entries, evidence_defs = parse_invariants(invariants_path, errors)
        names = [entry["name"] for entry in entries]
        duplicate_names = duplicate_values(names)
        if duplicate_names:
            errors.append(f"{pack}: duplicate predicate names: {', '.join(duplicate_names)}")

        deterministic = sum(1 for entry in entries if entry["mode"] == "deterministic")
        semantic = sum(1 for entry in entries if entry["mode"] == "semantic")
        deterministic_min, deterministic_max = PACK_DETERMINISTIC_LIMITS.get(
            pack, (MIN_DETERMINISTIC, MAX_DETERMINISTIC)
        )
        if not deterministic_min <= deterministic <= deterministic_max:
            errors.append(
                f"{pack}: expected {deterministic_min}-{deterministic_max} deterministic predicates, found {deterministic}"
            )
        if not MIN_SEMANTIC <= semantic <= MAX_SEMANTIC:
            errors.append(
                f"{pack}: expected {MIN_SEMANTIC}-{MAX_SEMANTIC} semantic predicates, found {semantic}"
            )

        validate_semantic_fallbacks(pack, entries, errors)
        validate_evidence(pack, entries, evidence_defs, errors)
        validate_pack_readme_coverage(pack_dir, set(names), errors)
        total_predicates += len(entries)
        total_fixtures += validate_fixtures(pack_dir, set(names), errors)

    if errors:
        print("Canon validation failed:", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1

    print(
        f"Validated {len(EXPECTED_PACKS)} packs, {total_predicates} predicates, and {total_fixtures} fixtures."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
