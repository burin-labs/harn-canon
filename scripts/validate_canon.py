#!/usr/bin/env python3
import calendar
import datetime as dt
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

EXPECTED_PACKS = (
    "c",
    "cpp",
    "csharp",
    "css",
    "dart",
    "dockerfile",
    "elixir",
    "go",
    "graphql",
    "harn",
    "haskell",
    "html",
    "java",
    "javascript",
    "json",
    "kotlin",
    "lua",
    "markdown",
    "php",
    "protobuf",
    "python",
    "r",
    "ruby",
    "rust",
    "scala",
    "shell",
    "sql",
    "swift",
    "terraform",
    "toml",
    "typescript",
    "xml",
    "yaml",
    "zig",
)

MIN_DETERMINISTIC = 5
MAX_DETERMINISTIC = 10
MIN_SEMANTIC = 2
MAX_SEMANTIC = 3
VALID_EXPECTS = {"Allow", "Warn", "Block"}

INVARIANT_RE = re.compile(
    r"@invariant\s*"
    r"@(?P<mode>deterministic|semantic)\s*"
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


def shifted_months(day, months):
    month_index = day.year * 12 + (day.month - 1) + months
    year, zero_based_month = divmod(month_index, 12)
    month = zero_based_month + 1
    capped_day = min(day.day, calendar.monthrange(year, month)[1])
    return dt.date(year, month, capped_day)


def parse_invariants(path, errors):
    text = path.read_text(encoding="utf-8")
    entries = [match.groupdict() for match in INVARIANT_RE.finditer(text)]
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

        if fixture.get("predicate") != fixture_path.stem:
            errors.append(f"{rel_path}: predicate must match fixture file name")

        cases = fixture.get("cases")
        if not isinstance(cases, list) or not cases:
            errors.append(f"{rel_path}: cases must be a non-empty list")
            continue

        expects = set()
        for index, case in enumerate(cases):
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
                if not isinstance(file_fixture.get("path"), str) or not file_fixture["path"]:
                    errors.append(f"{rel_path}: case {index} file {file_index} needs a path")
                if not isinstance(file_fixture.get("text"), str):
                    errors.append(f"{rel_path}: case {index} file {file_index} needs text")

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


def main():
    errors = []
    expected = set(EXPECTED_PACKS)
    actual = {path.name for path in ROOT.iterdir() if (path / "invariants.harn").is_file()}

    for pack in sorted(expected - actual):
        errors.append(f"{pack}: expected pack directory is missing")
    for pack in sorted(actual - expected):
        errors.append(f"{pack}: pack directory is not listed in EXPECTED_PACKS")

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
        duplicate_names = sorted({name for name in names if names.count(name) > 1})
        if duplicate_names:
            errors.append(f"{pack}: duplicate predicate names: {', '.join(duplicate_names)}")

        deterministic = sum(1 for entry in entries if entry["mode"] == "deterministic")
        semantic = sum(1 for entry in entries if entry["mode"] == "semantic")
        if not MIN_DETERMINISTIC <= deterministic <= MAX_DETERMINISTIC:
            errors.append(
                f"{pack}: expected {MIN_DETERMINISTIC}-{MAX_DETERMINISTIC} deterministic predicates, found {deterministic}"
            )
        if not MIN_SEMANTIC <= semantic <= MAX_SEMANTIC:
            errors.append(
                f"{pack}: expected {MIN_SEMANTIC}-{MAX_SEMANTIC} semantic predicates, found {semantic}"
            )

        validate_evidence(pack, entries, evidence_defs, errors)
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
