# Coding Standards

## Overall

- Do not write obvious comments
- KISS
- DRY
- Prefer refactorings over repeating the code
- Follow rules of the existing codebase
- Do not implement singleton classes; keep shared state as an explicit module-level instance (e.g. `default_config`) and keep classes instantiable.

## Python

- 4 spaces as indent
- Follow Black rules
- Import ordering compatible with ISort

## Writing Tests

- One assertion per test
- Test edge cases, successful and failure scenarios
- Prefer functional and integration tests over unit tests, but for libraries you can also make unit tests
- Create unit tests only for core AND important classes
