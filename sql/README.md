# SQL Seed Predicate Pack

This pack covers schema, migration, and query safety for raw SQL files. It targets review issues that an Archivist can catch cheaply on changed slices: implicit column lists, comma joins, table-wide DELETE/UPDATE statements, non-idempotent migration DDL, dynamic SQL that concatenates untrusted input, and foreign keys without supporting indexes.

## Stack Assumptions

- SQL source files use the `.sql` extension.
- Production paths exclude any path under `test/`, `tests/`, `testdata/`, `fixtures/`, `seed/`, or `seeds/`, and any file ending in `_test.sql`, `_seed.sql`, or `_fixture.sql`.
- Migration paths are detected by directory segments such as `migrations/`, `migration/`, `migrate/`, `changelog/`, `changesets/`, `flyway/`, `liquibase/`, or `sqitch/`. Predicates that only make sense for migrations (`migrations_use_if_not_exists`, `destructive_drops_use_if_exists`) restrict their scan to those paths.
- Deterministic predicates use file-text regex scans because Harn Flow does not yet expose a stable SQL AST query API; semantic predicates make a single judge call over changed SQL files.
- Predicates are dialect-aware where it matters: `migrations_use_if_not_exists`, `destructive_drops_use_if_exists`, and `index_on_fk` cover PostgreSQL and MySQL syntax variants and tolerate `CONCURRENTLY` for PostgreSQL index DDL.

## Predicate Coverage

| Predicate | Mode | Verdict | Purpose |
|---|---|---|---|
| `no_select_star` | deterministic | Block | Unqualified `SELECT *` in views and application queries breaks downstream consumers when columns are added or reordered. |
| `explicit_join_type` | deterministic | Block | Comma joins hide the intended cardinality and frequently degrade to accidental cross joins when a predicate is dropped. |
| `no_unbounded_delete_or_update` | deterministic | Block | `DELETE` and `UPDATE` without `WHERE` rewrite the whole table; `TRUNCATE` is the explicit operation for that. |
| `migrations_use_if_not_exists` | deterministic | Warn | `CREATE TABLE` and `CREATE INDEX` in migrations should tolerate a partially applied prior run. |
| `destructive_drops_use_if_exists` | deterministic | Warn | `DROP` in migrations should tolerate a partially applied prior run instead of erroring out mid-deploy. |
| `parameterized_queries_only` | semantic | Block | Dynamic SQL that interpolates user-controlled values is the leading vector for SQL injection. |
| `index_on_fk` | semantic | Block | Engines that do not auto-index foreign key columns (notably PostgreSQL) suffer table scans on `DELETE`/`UPDATE` of the referenced row. |

## Evidence

Evidence scanned on 2026-05-09.

- PostgreSQL docs: `CREATE VIEW`, `CREATE TABLE`, `CREATE INDEX`, `DROP TABLE`, `SELECT`, `UPDATE`, `DELETE`, `PREPARE`, table expressions, and constraint reference pages.
- MySQL Reference Manual 8.0: `CREATE TABLE`, `DROP TABLE`, foreign key reference, MySQL tips covering `--safe-updates` mode.
- Microsoft Learn T-SQL: `sp_executesql` reference for parameterized dynamic SQL on SQL Server.
- OWASP Cheat Sheet Series: SQL Injection Prevention Cheat Sheet (parameterized queries as primary defense).
- GitLab development docs: SQL guidelines (explicit columns over `SELECT *`).
- Holywell SQL Style Guide (`sqlstyle.guide`): explicit `JOIN` keyword preferred over comma-separated `FROM`.

## Known False Positives

- Regex predicates do not parse SQL. Comments containing keywords, dollar-quoted bodies, and CTE-heavy statements can fool the deterministic checks.
- `no_select_star` flags any `SELECT * FROM ...`, including `INSERT INTO target SELECT * FROM staging` patterns that are intentional in copy migrations. Suppress locally once the predicate runtime supports it.
- `explicit_join_type` flags any comma between table names in a `FROM` clause. `FROM (subquery), other` is a rare false negative because `(` is not part of the leading-token character class.
- `no_unbounded_delete_or_update` matches statement-by-statement up to the first `;`. SQL with semicolons inside string literals or dollar-quoted bodies can shift statement boundaries; in those cases prefer the semantic `parameterized_queries_only` reading or split the file.
- `migrations_use_if_not_exists` and `destructive_drops_use_if_exists` only inspect migration paths and only the `TABLE`/`INDEX`/`VIEW`/`MATERIALIZED VIEW`/`TYPE`/`SCHEMA`/`SEQUENCE` object kinds. `CREATE OR REPLACE VIEW` and `CREATE FUNCTION` are intentionally out of scope.
- `index_on_fk` is conservative — MySQL InnoDB auto-creates the supporting index for inline FK constraints, and the rubric instructs the judge to allow that case. PostgreSQL does not, which is the primary motivating dialect.

## Fixtures

Each fixture in `fixtures/` contains one blocked or warned example and one allowed example for the corresponding predicate. The fixture shape matches the harn-canon convention:

```json
{
  "predicate": "name",
  "cases": [
    {"expect": "Block", "files": [{"path": "schema/views/active_users.sql", "text": "..."}]},
    {"expect": "Allow", "files": [{"path": "schema/views/active_users.sql", "text": "..."}]}
  ]
}
```
