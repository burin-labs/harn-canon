SQL Seed Predicate Pack (v0)

This pack defines basic SQL safety and style rules.

## RULES
- AVOID SELECT * for clarity and performance
- USE EXPLICIT JOINS instead of COMMA JOINS
- Prevent SQL injection via parameterized queries
- Index foreign key columns

## Fixtures
- fixtures/allow.sql -> example that should pass
- fixtures/block.sql -> example that should blocked

## Why
Improves performance, security, and maintainability

## Sources (evidence)
- postgre SQL documentation (SELECT, JOINS, Indexes)
- OWASP SQL Injection Prevention cheat sheet