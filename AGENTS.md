# AGENTS.md

## Preferences
- When I ask to unify or simplify an API/naming, do not keep backward-compatibility aliases, deprecated wrappers, or transition shims unless I explicitly ask for them.
- Prefer full cleanup (code + tests) over soft migrations when renaming parameters/functions, unless backward compatibility is explicitly required.
- Follow project coding style tools (`black`, `isort`) for Python changes unless I explicitly say otherwise.
- Prefer running `isort` and `black` after Python edits (as fixers or checks) so source style stays clean; if the tools are unavailable, say so explicitly.
- If `black`/`isort` (or other dev tools I ask for) are missing, create a local venv in `.env` and install dev deps from `pyproject.toml`. Prefer `make dev-setup`, but if sandbox restrictions block Makefile targets, try running the underlying command directly (e.g. `pip install -e ".[dev]"`) from the venv. Then run the tools from that venv.
- Prefer project `Makefile` targets when available (for example `make dev-setup`, `make fmt`, `make lint`, `make check`, `make test-pytest`) instead of ad-hoc commands.
- If a required command cannot run due to sandbox/network restrictions, ask the operator to run it locally and share the output; keep the request compact and concrete.
- Prefer `KISS` and `DRY`: keep solutions simple, avoid duplication, and do not overengineer.
- Keep comments minimal and useful; add comments only where the code is not obvious.
- Ask before doing non-trivial refactors (structure changes, renames across files, abstraction cleanup) unless I explicitly requested a refactor.
- Add or update tests for behavior changes and bug fixes; for trivial mechanical edits, ask before expanding test scope.
- When high-level API changes (function names, parameters, usage patterns), update `README.md` usage examples in the same change.
- When behavior, public API, CLI output, or configuration semantics change, update `docs/` in the same change so Sphinx documentation stays current.
- Validate changes before finishing: run a quick syntax check and execute relevant tests when available; if something cannot be run, state it explicitly.
- Prefer an Extreme Programming style when it makes sense: for bug fixes, first add a test that reproduces the bug, then implement the fix, then run checks/tests to confirm it.
